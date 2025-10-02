from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime, timedelta
import random
from sqlalchemy import text, select, func, or_
from app.models import StatusHealth, LublinoHousesId
from app.schemas import (
    DashboardMetrics,
    HouseListItem,
    HouseDetail
)

REGION_ID_TO_NAME: Dict[str, str] = {
    "lublino": "Район Люблино",
}
async def get_incident_history_for_llm(db: AsyncSession, house_id: str, hours_back: int = 24) -> List[Dict]:
    """
    Получает историю инцидентов для конкретного дома за последние N часов.
    """
    query = text("""
        SELECT
          to_char(time_5min, 'DD/MM HH24:MI') AS "time_str",
          diffr_prcnt_1h AS "change_1h_percent",
          type_incdnt,
          comment_incdnt AS "comment"
        FROM public.incident_hist_2
        WHERE id_house = :house_id
          AND time_5min >= now()
          AND time_5min <= now() 
          AND type_incdnt IN (1, 3) 
        ORDER BY time_5min DESC; 
    """)
    try:
        query_formatted = query.text.replace(':hours_back', str(int(hours_back)))
        query_final = text(query_formatted)

        result = await db.execute(query_final, {"house_id": int(house_id)})
        rows = result.fetchall()
        return [
            {
                "time_str": row.time_str,
                "change_1h_percent": row.change_1h_percent,
                "type_incdnt_num": row.type_incdnt,
                "type_incdnt_str": "Инцидент" if row.type_incdnt == 1 else "Предупреждение" if row.type_incdnt == 3 else f"Тип {row.type_incdnt}",
                "comment": row.comment
            }
            for row in rows
        ]
    except Exception as e:
        print(f"Error getting incident history for house {house_id}: {e}")
        return []

async def get_regional_incident_stats(db: AsyncSession, region_id: str, hours_back: int = 24) -> Dict:
    """
    Получает ТОП-10 последних инцидентов и предупреждений по региону за последние N часов.
    Использует серверное время PostgreSQL для фильтрации, исключая будущие даты.
    Возвращает список событий с адресом, временем, типом и комментарием.
    type_incdnt: 1 - Инцидент, 3 - Предупреждение, 2 - Нет отклонения (не включается).
    """
    query = text("""
        SELECT
          lhi.simple_address, -- Адрес дома
          to_char(ih.time_5min, 'DD/MM HH24:MI') AS "time_str", -- Время события (строка!)
          ih.diffr_prcnt_1h AS "change_1h_percent", -- Изменение за 1ч
          ih.type_incdnt, -- Тип инцидента (число)
          ih.comment_incdnt -- Комментарий
        FROM public.incident_hist_2 ih
        JOIN lublino_houses_id lhi ON ih.id_house = lhi.id_house
        WHERE ih.id_house IN (SELECT id_house FROM lublino_houses_id) -- Ограничение регионом
          AND ih.time_5min >= now() - INTERVAL ':hours_back hours' -- Фильтр по времени: не раньше N часов назад
          AND ih.time_5min <= now() -- Фильтр по времени: не позже текущего времени (исключаем будущее)
          AND ih.type_incdnt IN (1, 3) -- Только инциденты (1) и предупреждения (3)
        ORDER BY ih.time_5min DESC -- Сортировка от новых (ближе к now()) к старым
        LIMIT 10 -- Ограничиваем 10 последними (в пределах фильтра)
    """)

    try:
        query_formatted = query.text.replace(':hours_back', str(int(hours_back)))
        query_final = text(query_formatted)

        result = await db.execute(query_final)
        rows = result.fetchall()

        recent_incidents_list = []
        incident_count = 0
        warning_count = 0
        latest_time_obj = None # Храним как datetime object

        for row in rows:
            # Подсчитываем типы
            if row.type_incdnt == 1:
                incident_count += 1
            elif row.type_incdnt == 3:
                warning_count += 1

            # Отслеживаем самое последнее время (первый элемент из-за ORDER BY DESC)
            # row.time_str - строка в формате 'DD/MM HH24:MI'
            # row.time_str теперь гарантированно <= now() и >= now() - INTERVAL
            if latest_time_obj is None and row.time_str:
                # Преобразуем строку в datetime object
                try:
                    latest_time_obj = datetime.strptime(row.time_str, '%d/%m %H:%M')
                except ValueError as ve:
                    print(f"Warning: Could not parse time string '{row.time_str}': {ve}")
                    continue 

            type_str_map = {1: "Инцидент", 3: "Предупреждение"}
            type_str = type_str_map.get(row.type_incdnt, f"Тип {row.type_incdnt}")

            recent_incidents_list.append({
                "address": row.simple_address or "Адрес не указан",
                "time_str": row.time_str, 
                "change_1h_percent": row.change_1h_percent,
                "type_incdnt_num": row.type_incdnt, 
                "type_incdnt_str": type_str, 
                "comment_incdnt": row.comment_incdnt or "Комментарий отсутствует"
            })

        total_events = len(recent_incidents_list)
        latest_time_str_for_summary = latest_time_obj.strftime('%d/%m %H:%M') if latest_time_obj else 'Нет данных'
        summary = f"Всего инцидентов и предупреждений за последние {hours_back} ч: {total_events}. " \
                  f"Инциденты (1): {incident_count}, Предупреждения (3): {warning_count}. " \
                  f"Последний инцидент/предупреждение: {latest_time_str_for_summary}."

        return {
            "total_incidents_and_warnings": total_events,
            "incident_count": incident_count,
            "warning_count": warning_count,
            "latest_incident_or_warning_time": latest_time_obj.isoformat() if latest_time_obj else None,
            "recent_incidents_list": recent_incidents_list, 
            "summary": summary
        }

    except Exception as e:
        print(f"Error getting regional incident stats for region {region_id}: {e}")
        return {
            "total_incidents_and_warnings": 0,
            "incident_count": 0,
            "warning_count": 0,
            "latest_incident_or_warning_time": None,
            "recent_incidents_list": [],
            "summary": f"Ошибка получения статистики инцидентов за последние {hours_back} ч."
        }

async def get_water_data_for_llm(db: AsyncSession, house_id: str) -> Dict:
    """
    Получает последние данные по расходу и отклонениям и прогноз ХВС для LLM
    """
    queries = {
        "consumption_1h": f"""
            SELECT time_1hour, water_cold, water_hot
            FROM public.water_consump_hot_1h
            WHERE id_house = :house_id
            ORDER BY time_1hour DESC
            LIMIT 24
        """,
        "diffr_1h": f"""
            SELECT time_1hour, diffr_ratio
            FROM public.water_diffr_coldhot_1h
            WHERE id_house = :house_id
            ORDER BY time_1hour DESC
            LIMIT 24
        """,
        "forecast_cold_water_24h_hourly": f"""
            SELECT
              ds AS "time",
              yhat AS "forecast_cold_water_value",
              '(прогноз)' AS "series_type"
            FROM public.water_forecast_all
            WHERE id_house = :house_id
              AND ds >= now() AT TIME ZONE 'UTC' -- Только будущие
              AND ds < now() AT TIME ZONE 'UTC' + INTERVAL '1 day' -- Ограничение 24 часами вперед
              AND EXTRACT(MINUTE FROM ds AT TIME ZONE 'UTC') = 0 -- Только на полный час (00 минут)
            ORDER BY ds ASC -- Сортировка по возрастанию времени
            -- LIMIT 24 -- Необязательно, так как фильтр по 24ч и по часам даст максимум 24 записи
        """
    }
    data = {}
    for key, query in queries.items():
        try:
            result = await db.execute(text(query), {"house_id": int(house_id)})
            rows = result.fetchall()
            # Обработка результата
            if key == "forecast_cold_water_24h_hourly":
                # Для прогноза структура строки может отличаться
                data[key] = [
                    {
                        "time": row.time.isoformat() if hasattr(row.time, 'isoformat') else str(row.time),
                        "values": {"forecast_cold_water_value": row.forecast_cold_water_value, "series_type": row.series_type}
                    }
                    for row in rows
                ]
            else:
                # Существующая логика для других типов данных
                # Используем result.keys()._keys для получения имен столбцов
                column_names = list(result.keys())
                data[key] = [
                    {
                        "time": row[0].isoformat() if hasattr(row[0], 'isoformat') else str(row[0]),
                        "values": {k: v for k, v in zip(column_names[1:], row[1:])} 
                    }
                    for row in rows
                ]
        except Exception as e:
            print(f"Error getting {key} data: {e}")
            data[key] = []
    return data

async def get_regional_forecast_cold_water_24h_hourly_random(db: AsyncSession, num_houses: int = 5) -> Dict:
    """
    Получает прогнозные значения ХВС для N рандомных домов из lublino_houses_id на ближайшие 24 часа, отфильтрованные по полным часам.
    """
    # Шаг 1: Получить список всех id_house из lublino_houses_id
    try:
        all_houses_query = text("SELECT id_house FROM lublino_houses_id")
        all_houses_result = await db.execute(all_houses_query)
        all_house_ids = [row.id_house for row in all_houses_result.fetchall()]

        if not all_house_ids:
            print("No houses found in lublino_houses_id.")
            return {
                "total_forecasts": 0,
                "min_forecast_time": None,
                "max_forecast_time": None,
                "forecast_list": [],
                "summary": "Нет домов для получения прогноза.",
                "selected_house_ids": [] # Добавим список выбранных ID для прозрачности
            }

        # Шаг 2: Выбрать N рандомных id_house (или все, если их меньше N)
        selected_house_ids = random.sample(all_house_ids, min(num_houses, len(all_house_ids)))
        print(f"Selected random house IDs for forecast: {selected_house_ids}") # Логирование

        # Шаг 3: Подготовить параметры для IN в основном запросе
        # SQLAlchemy не очень любит списки напрямую в text(), поэтому используем строку
        house_ids_str = ','.join(map(str, selected_house_ids))

        # Шаг 4: Основной запрос к water_forecast_all с фильтрацией по выбранным ID
        query = text(f"""
            SELECT
              lhi.simple_address, -- Адрес дома
              to_char(wf.ds, 'DD/MM HH24:MI') AS "time_str", -- Время прогноза (строка!)
              wf.yhat AS "forecast_cold_water_value"
            FROM public.water_forecast_all wf
            JOIN lublino_houses_id lhi ON wf.id_house = lhi.id_house
            WHERE lhi.id_house IN ({house_ids_str}) -- Фильтр по выбранным рандомным ID
              AND wf.ds >= now() AT TIME ZONE 'UTC' -- Только будущие
              AND wf.ds < now() AT TIME ZONE 'UTC' + INTERVAL '1 day' -- Ограничение 24 часами вперед
              AND EXTRACT(MINUTE FROM wf.ds AT TIME ZONE 'UTC') = 0 -- Только на полный час (00 минут)
            ORDER BY wf.ds ASC, lhi.simple_address ASC -- Сортировка по времени, затем по адресу
            -- LIMIT 100 -- Опционально: ограничить количество возвращаемых записей, если слишком много
        """)
        result = await db.execute(query)
        rows = result.fetchall()

        forecast_list = []
        min_forecast_time = None
        max_forecast_time = None
        total_forecasts = 0

        for row in rows:
            total_forecasts += 1
            # Отслеживаем временные границы прогноза
            if min_forecast_time is None:
                min_forecast_time = row.time_str
            # max_forecast_time обновляется на последнюю строку после сортировки ASC
            max_forecast_time = row.time_str

            forecast_list.append({
                "address": row.simple_address or "Адрес не указан",
                "time_str": row.time_str,
                "forecast_value": row.forecast_cold_water_value,
            })

        summary = f"Всего прогнозов ХВС для {len(selected_house_ids)} рандомных домов на ближайшие 24 ч (1-час интервал): {total_forecasts}. Прогноз с {min_forecast_time} до {max_forecast_time}."

        return {
            "total_forecasts": total_forecasts,
            "min_forecast_time": min_forecast_time,
            "max_forecast_time": max_forecast_time,
            "forecast_list": forecast_list,
            "summary": summary,
            "selected_house_ids": selected_house_ids # Возвращаем для информации
        }
    except Exception as e:
        print(f"Error getting regional forecast stats for random houses: {e}")
        return {
            "total_forecasts": 0,
            "min_forecast_time": None,
            "max_forecast_time": None,
            "forecast_list": [],
            "summary": f"Ошибка получения прогнозных данных ХВС для рандомных домов: {e}",
            "selected_house_ids": []
        }


async def get_real_dashboard_metrics(db: AsyncSession, region_id: str, days: int) -> DashboardMetrics:
    """Получить метрики дашборда из реальных данных"""
    
    # Подсчет домов по статусу здоровья
    red_count = await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Red")
    )
    red = red_count.scalar() or 0
    
    yellow_count = await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Yellow")
    )
    yellow = yellow_count.scalar() or 0
    
    green_count = await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Green")
    )
    green = green_count.scalar() or 0
    
    in_work_count = await db.execute(
        select(func.count(StatusHealth.id_house)).where(
            StatusHealth.status_incident.in_(["New", "Work", "Repair"])
        )
    )
    in_work = in_work_count.scalar() or 0
    
    # Сбои только за текущий день (сегодня)
    from datetime import date
    today = date.today()
    
    # Подсчитываем только сбои за сегодня
    today_failures = await db.execute(
        select(func.count(StatusHealth.id_house)).where(
            StatusHealth.house_health.in_(["Red", "Yellow"])
        )
    )
    total_current_failures = today_failures.scalar() or 0
    
    # Обработанные сегодня
    processed_current = await db.execute(
        select(func.count(StatusHealth.id_house)).where(
            or_(
                StatusHealth.status_incident == "Work",
                StatusHealth.status_incident == "Repair"
            )
        )
    )
    processed = processed_current.scalar() or 0
    
    return DashboardMetrics(
        region_id=region_id,
        region_name=REGION_ID_TO_NAME.get(region_id, "Неизвестный район"),
        counts={
            "red": red,
            "yellow": yellow,
            "green": green,
            "in_work": in_work,
            "total_current_failures": total_current_failures,
            "processed_current": processed,
        },
        period_days=days,
    )

async def get_real_house_list(
    db: AsyncSession,
    region_id: str,
    status: Optional[str] = None,
    incident_status: Optional[str] = None,
    search: Optional[str] = None,
) -> List[HouseListItem]:
    """Получить список домов из реальных данных с объединением таблиц"""
    
    # Базовый запрос с объединением таблиц (включаем все статусы)
    query = select(
        StatusHealth.id_house,
        StatusHealth.unom,
        StatusHealth.status_incident,
        StatusHealth.house_health,
        LublinoHousesId.simple_address,
        LublinoHousesId.address,
        LublinoHousesId.district
    ).select_from(
        StatusHealth
    ).join(
        LublinoHousesId, StatusHealth.id_house == LublinoHousesId.id_house
    )
    
    # Применяем фильтры
    if status:
        if status == "red":
            query = query.where(StatusHealth.house_health == "Red")
        elif status == "yellow":
            query = query.where(StatusHealth.house_health == "Yellow")
        elif status == "green":
            query = query.where(StatusHealth.house_health == "Green")
        elif status == "in_work":
            query = query.where(
                StatusHealth.status_incident.in_(["New", "Work", "Repair"])
            )
    
    if incident_status:
        # Маппинг русских статусов на английские
        status_mapping = {
            "В работе": "Work",
            "В ремонте": "Repair",
            "Новый": "New",
            "Решен": "Resolved",
            "Статус не задан": None
        }
        english_status = status_mapping.get(incident_status, incident_status)
        if english_status is None:
            query = query.where(StatusHealth.status_incident.is_(None))
        else:
            query = query.where(StatusHealth.status_incident == english_status)
    
    if search:
        query = query.where(
            or_(
                LublinoHousesId.simple_address.ilike(f"%{search}%"),
                LublinoHousesId.address.ilike(f"%{search}%")
            )
        )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Преобразуем в формат HouseListItem
    houses = []
    for row in rows:
        # Маппинг статусов
        status_mapping = {
            "Red": "red",
            "Yellow": "yellow", 
            "Green": "green"
        }
        
        # Маппинг статусов
        status_mapping = {
            "Red": "red",
            "Yellow": "yellow", 
            "Green": "green"
        }
        
        # Если есть инцидент, то статус "in_work"
        if row.status_incident in ("New", "Work", "Repair"):
            mapped_status = "in_work"
        else:
            mapped_status = status_mapping.get(row.house_health, "green")
        
        # Маппинг статуса инцидента для валидации
        incident_status_mapping = {
            "Work": "В работе",
            "Repair": "В ремонте",
            "New": "Новый",
            "Resolved": "Решен",
            None: "Статус не задан"
        }
        
        houses.append(HouseListItem(
            house_id=str(row.id_house),
            address=row.simple_address or row.address or "Адрес не указан",
            region=REGION_ID_TO_NAME.get(region_id, "Неизвестный район"),
            status=mapped_status,
            last_failure_date=None,  # В реальных данных нет даты последней проблемы
            incident_status=incident_status_mapping.get(row.status_incident, "В работе"),
            unom=str(row.unom),
        ))
    
    return houses

async def get_real_house_detail(db: AsyncSession, house_id: str) -> Optional[HouseDetail]:
    """Получить детальную информацию о доме из реальных данных"""
    
    query = select(
        StatusHealth.id_house,
        StatusHealth.unom,
        StatusHealth.status_incident,
        StatusHealth.house_health,
        LublinoHousesId.simple_address,
        LublinoHousesId.address,
        LublinoHousesId.district,
        LublinoHousesId.n_fias,
        LublinoHousesId.nreg
    ).select_from(
        StatusHealth,
    ).join(
        LublinoHousesId, StatusHealth.id_house == LublinoHousesId.id_house
    ).where(StatusHealth.id_house == int(house_id))
    
    result = await db.execute(query)
    row = result.fetchone()
    
    if not row:
        return None
    
    # Маппинг статусов
    status_mapping = {
        "Red": "red",
        "Yellow": "yellow", 
        "Green": "green"
    }
    
    # Маппинг статуса инцидента
    incident_status_mapping = {
        "Work": "В работе",
        "Repair": "В ремонте",
        "New": "Новый",
        "Resolved": "Решен",
        None: "Статус не задан"
    }
    
    if row.status_incident in ("New", "Work", "Repair"):
        mapped_status = "in_work"
    else:
        mapped_status = status_mapping.get(row.house_health, "green")
    
    # Убираем фиктивные данные для серий
    
    return HouseDetail(
        house_id=house_id,
        address=row.simple_address or row.address or "Адрес не указан",
        simple_address=row.simple_address,
        region=REGION_ID_TO_NAME.get("lublino", "Район Люблино"),
        status=mapped_status,
        incident_status=incident_status_mapping.get(row.status_incident, "Статус не задан"),
        last_failure_date=None,
        status_valid_until=None,
        status_reason=None,
        fias=str(row.n_fias),
        unom=str(row.unom),
        nreg=row.nreg,
    )

async def get_full_llm_context(db: AsyncSession, region_id: str):
    """Получить полный контекст для LLM: статистика + проблемные дома"""
    
    # 1. Общее количество домов в районе
    total_houses = await db.execute(
        select(func.count(LublinoHousesId.id_house))
    )
    total = total_houses.scalar() or 0

    # 2. Количество домов по статусу здоровья
    red = (await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Red")
    )).scalar() or 0

    yellow = (await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Yellow")
    )).scalar() or 0

    green = (await db.execute(
        select(func.count(StatusHealth.id_house)).where(StatusHealth.house_health == "Green")
    )).scalar() or 0

    # 3. Дома с активными инцидентами
    in_work = (await db.execute(
        select(func.count(StatusHealth.id_house)).where(
            StatusHealth.status_incident.in_(["New", "Work", "Repair"])
        )
    )).scalar() or 0

    # 4. Проблемные дома (как раньше)
    query = select(
        StatusHealth.id_house,
        StatusHealth.unom,
        StatusHealth.status_incident,
        StatusHealth.house_health,
        LublinoHousesId.simple_address,
        LublinoHousesId.address,
    ).select_from(StatusHealth).join(
        LublinoHousesId, StatusHealth.id_house == LublinoHousesId.id_house
    ).where(
        or_(
            StatusHealth.house_health.in_(["Red", "Yellow"]),
            StatusHealth.status_incident.in_(["New", "Work", "Repair"])
        )
    )

    result = await db.execute(query)
    problem_rows = result.fetchall()

    problem_houses = []
    for row in problem_rows[:100]:  # Ограничим 100
        status_text = "Критический инцидент" if row.house_health == "Red" else "Предупреждение"
        incident_text = row.status_incident or "Статус не задан"
        addr = row.simple_address or row.address or "Адрес неизвестен"
        problem_houses.append(f"{addr} (УНОМ: {row.unom}) — {status_text}, инцидент: {incident_text}")

    return {
        "region": REGION_ID_TO_NAME.get(region_id, "Неизвестный район"),
        "total_houses": total,
        "status_breakdown": {
            "red": red,
            "yellow": yellow,
            "green": green,
            "in_work": in_work,
        },
        "problem_houses_list": problem_houses,
    }


async def get_real_llm_context(db: AsyncSession, region_id: str):
    """Получить контекст для LLM из реальных данных - только дома с проблемами"""
    
    # Получаем только дома с проблемами (Red, Yellow) и активными инцидентами
    query = select(
        StatusHealth.id_house,
        StatusHealth.unom,
        StatusHealth.status_incident,
        StatusHealth.house_health,
        LublinoHousesId.simple_address,
        LublinoHousesId.address,
        LublinoHousesId.district
    ).select_from(
        StatusHealth
    ).join(
        LublinoHousesId, StatusHealth.id_house == LublinoHousesId.id_house
    ).where(
        or_(
            StatusHealth.house_health.in_(["Red", "Yellow"]),
            StatusHealth.status_incident.isnot(None)
        )
    )
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Формируем краткий контекст для экономии токенов
    houses = []
    for row in rows:
        status_text = "Критический инцидент" if row.house_health == "Red" else "Предупреждение" if row.house_health == "Yellow" else "Норма"
        incident_text = row.status_incident or "Статус не задан"
        
        # Краткий формат для экономии токенов
        houses.append(f"{row.simple_address or row.address} - {status_text} ({incident_text})")
    
    return {
        "region": REGION_ID_TO_NAME.get(region_id, "Неизвестный район"),
        "total_problem_houses": len(houses),
        "houses": houses[:100]  # Увеличиваем до 100 домов для более полной информации
    }
