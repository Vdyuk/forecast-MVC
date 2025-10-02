from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from sqlalchemy import text, select
from fastapi import HTTPException
import httpx
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from .schemas import (
    DashboardMetrics,
    HouseListItem,
    HouseDetail,
    LLMQuestionRequest,
)

from .real_data import (
    REGION_ID_TO_NAME,
    get_full_llm_context,
    get_incident_history_for_llm,
    get_real_dashboard_metrics,
    get_real_house_list,
    get_real_house_detail,
    get_real_llm_context,
    get_regional_forecast_cold_water_24h_hourly_random,
    get_regional_incident_stats,
    get_water_data_for_llm,
)
from .models import LublinoHousesId, StatusHealth

app = FastAPI(title="GVS Monitoring API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv() 

# Email конфигурация
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.mail.ru")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
NOTIFICATION_EMAILS = [email.strip() for email in os.getenv("NOTIFICATION_EMAILS", "").split(",") if email.strip()]

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def format_regional_forecasts_for_llm(forecast_list: List[Dict]) -> str:
    """
    Форматирует список прогнозов ХВС для LLM контекста.
    """
    if not forecast_list:
        return "Нет прогнозных данных по ХВС для выбранных рандомных домов на ближайшие 24 часа (1-час интервал)."
    lines = []
    for item in forecast_list[:20]: # Ограничиваем, чтобы не перегружать контекст
        addr = item["address"]
        time_str = item["time_str"]
        value = item["forecast_value"]
        lines.append(f"- {addr} ({time_str}): {value} (прогноз)")
    return "\n".join(lines)


def send_email_notification(house_id: str, address: str, status: str, incident_status: str):
    """
    Отправка email уведомления о новом инциденте
    """
    if not EMAIL_USER or not EMAIL_PASSWORD or not NOTIFICATION_EMAILS:
        print(f"Email configuration not set, skipping notification")
        print(f"EMAIL_USER: {EMAIL_USER is not None}")
        print(f"EMAIL_PASSWORD: {EMAIL_PASSWORD is not None}")
        print(f"NOTIFICATION_EMAILS: {NOTIFICATION_EMAILS}")
        return
    
    # Определяем, нужно ли отправлять уведомление (только для проблемных статусов)
    if status.lower() not in ['red', 'yellow']:
        print(f"Skipping notification for status: {status}")
        return
    
    # Маппинг статусов на русский
    status_mapping = {
        'red': 'Критический',
        'yellow': 'Проблемный', 
        'green': 'В норме'
    }
    
    # Маппинг статусов инцидента на русский
    incident_mapping = {
        'New': 'Новый',
        'Work': 'В работе',
        'Repair': 'В ремонте',
        'Resolved': 'Решен',
        'None': 'Статус не задан'
    }
    
    # Преобразуем статусы в русские
    russian_status = status_mapping.get(status.lower(), status)
    russian_incident_status = incident_mapping.get(incident_status, incident_status)
    
    subject = f"🚨 Новый инцидент в доме - {address}"
    
    body = f"""
    <html>
    <body>
        <h2>🚨 Новый инцидент в доме</h2>
        <p><strong>ID дома:</strong> {house_id}</p>
        <p><strong>Адрес:</strong> {address}</p>
        <p><strong>Статус дома:</strong> {russian_status}</p>
        <p><strong>Статус инцидента:</strong> {russian_incident_status}</p>
        <p><strong>Время:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <hr>
        <p>Это автоматическое уведомление от системы мониторинга ГВС.</p>
    </body>
    </html>
    """
    
    try:
        print(f"Attempting to send email to: {NOTIFICATION_EMAILS}")
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = ", ".join(NOTIFICATION_EMAILS)
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Выбираем метод подключения в зависимости от порта
        if SMTP_PORT == 465:
            # SSL
            print(f"Using SSL connection to {SMTP_SERVER}:{SMTP_PORT}")
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)
        else:
            # TLS
            print(f"Using TLS connection to {SMTP_SERVER}:{SMTP_PORT}")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)
        
        print(f"Email notification sent successfully for house {house_id}")
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        print("Check your email credentials and app password settings")
    except smtplib.SMTPRecipientsRefused as e:
        print(f"SMTP Recipients Refused Error: {e}")
        print(f"Check if recipient emails are valid: {NOTIFICATION_EMAILS}")
    except smtplib.SMTPConnectError as e:
        print(f"SMTP Connection Error: {e}")
        print(f"Check if {SMTP_SERVER}:{SMTP_PORT} is accessible")
    except Exception as e:
        print(f"Failed to send email notification: {e}")
        import traceback
        traceback.print_exc()
        

def format_regional_incidents_for_llm(incidents_list: List[Dict]) -> str:
    """
    Форматирует список последних инцидентов/предупреждений для LLM контекста.
    """
    if not incidents_list:
        return "Нет данных о последних инцидентах или предупреждениях за последние 24 часа."
    # Показываем ВСЕ записи из top-10
    lines = []
    for item in incidents_list:
        addr = item["address"]
        time_str = item["time_str"]
        type_str = item["type_incdnt_str"]
        comment_str = item["comment_incdnt"]
        # change_str = f"{item['change_1h_percent']:.2f}%" if item['change_1h_percent'] is not None else "N/A"
        # lines.append(f"- {addr} ({time_str}): {type_str} (Изменение: {change_str}) - {comment_str}")
        lines.append(f"- {addr} ({time_str}): {type_str} - {comment_str}")
    return "\n".join(lines)


def format_incident_history(history: List[Dict]) -> str:
    """
    Форматирует историю инцидентов для LLM контекста (для конкретного дома).
    """
    if not history:
        return "Нет данных об инцидентах за последние 24 часа."
    # Показываем ВСЕ записи за период
    lines = []
    for item in history: # Показываем все записи
        time_str = item["time_str"]
        type_str = item["type_incdnt_str"]
        change_str = f"{item['change_1h_percent']:.2f}%" if item['change_1h_percent'] is not None else "N/A"
        comment_str = item["comment"] or "Комментарий отсутствует"
        lines.append(f"- {time_str}: {type_str} (Изменение: {change_str}) - {comment_str}")
    return "\n".join(lines)


@app.post("/api/houses/{house_id}/ask-llm")
async def ask_llm_about_house(house_id: str, payload: LLMQuestionRequest, db: AsyncSession = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    # Получаем данные дома из реальной БД
    house = await get_real_house_detail(db, house_id)
    if not house:
        raise HTTPException(status_code=404, detail="House not found")

    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY не задан в .env")

    # Получаем данные по расходу и отклонениям
    water_data = await get_water_data_for_llm(db, house_id)
    incident_history = await get_incident_history_for_llm(db, house_id, hours_back=720)
    # Подготавливаем краткий контекст для экономии токенов
    context = f"""Дом: {house.address}
Статус: {house.status}
Инцидент: {house.incident_status}
УНОМ: {house.unom}
Последние данные по расходу воды (1-час интервал):
{format_water_data(water_data.get('consumption_1h', []))}
Последние данные по отклонениям (1-час интервал):
{format_water_data(water_data.get('diffr_1h', []))}
Прогнозные данные по расходу ХВС (на ближайшие 24 часов, 1-час интервал):
{format_water_data(water_data.get('forecast_cold_water_24h_hourly', []))}
История инцидентов (последний месяц):
{format_incident_history(incident_history)}
"""

    prompt = f"""Ты — эксперт по мониторингу ГВС. Ответь кратко на русском языке.

Названия статусов нужно возвращать на русском Repair - В ремонте, New - Новый, Resolved - Решен. Work - В работе. None - Статус не задан.

Ответ должен быть кратким и не превышать 1000 токенов. Если информация объёмная — сожми её, сохранив суть.

Если вопрос не относится к теме ГВС или дома — вежливо откажись отвечать.

ИНСТРУКЦИИ:
- Не выдумывай данные.
- Если информации недостаточно — скажи: "Недостаточно данных".
- Используй Markdown: **жирный** для заголовков, списки для перечислений.

Данные: {context}

Вопрос: "{question}"
"""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",  # УБРАЛ ПРОБЕЛЫ
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-chat-v3.1:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 1500
                }
            )
            if resp.status_code != 200:
                error_msg = resp.json().get("error", {}).get("message", "Unknown error")
                print(f"OpenRouter error {resp.status_code}: {error_msg}")
                raise HTTPException(status_code=502, detail=f"OpenRouter error: {error_msg}")

            answer = resp.json()["choices"][0]["message"]["content"].strip()
            return {"answer": answer}

    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации ответа")


def format_water_data(data: List[Dict]) -> str:
    """
    Форматирует данные для LLM контекста
    """
    if not data:
        return "Нет данных"
    # Показываем ВСЕ записи за день
    lines = []
    for item in data:  # Убрали [:5]
        time_str = item["time"]
        values = item.get("values", {})
        # Форматирование может зависеть от структуры values
        # Если есть 'series_type', можно его учитывать
        values_str_parts = []
        for k, v in values.items():
            if v is not None:
                if k == 'series_type':
                    values_str_parts.append(f"{v}") # Добавляем тип серии, например, (прогноз)
                else:
                    values_str_parts.append(f"{k}: {v}")
        values_str = ", ".join(values_str_parts)
        lines.append(f"- {time_str}: {values_str}")
    return "\n".join(lines)

@app.post("/api/ask-llm")
async def ask_llm_about_all_houses(payload: LLMQuestionRequest, db: AsyncSession = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY не задан в .env")
    # Получаем ПОЛНЫЙ контекст
    ctx = await get_full_llm_context(db, "lublino")
    # Получаем ТОП-10 последних инцидентов по региону
    incident_stats = await get_regional_incident_stats(db, "lublino", hours_back=24)
    forecast_stats = await get_regional_forecast_cold_water_24h_hourly_random(db, num_houses=5)
    print(forecast_stats)
    # Формируем информативный контекст
    stats = ctx["status_breakdown"]
    context = f"""Район: {ctx['region']}
Всего домов: {ctx['total_houses']}
Статусы домов:
- 🔴 Критические инциденты (Red): {stats['red']}
- 🟡 Предупреждения (Yellow): {stats['yellow']}
- 🟢 В норме (Green): {stats['green']}
- 🛠️ В работе (инциденты): {stats['in_work']}
Статистика инцидентов за последние 24 часа: {incident_stats.get('summary', 'Нет данных')}
Названия статусов нужно возвращать на русском Repair - В ремонте, New - Новый, Resolved - Решен. Work - В работе. None - Статус не задан.
ТОП-10 последних инцидентов и предупреждений (последние 24 часа):
{format_regional_incidents_for_llm(incident_stats.get('recent_incidents_list', []))}
Прогнозные данные ХВС (на ближайшие 24 часа, 1-час интервал): {forecast_stats.get('summary', 'Нет данных')}
Примеры прогнозов (первые 20):
{format_regional_forecasts_for_llm(forecast_stats.get('forecast_list', []))}
Дома с проблемами (примеры):
{chr(10).join(ctx['problem_houses_list']) if ctx['problem_houses_list'] else 'Нет домов с проблемами'}"""
    prompt = f"""Ты — эксперт по мониторингу ГВС. Ответь кратко на русском языке.
Ответ должен быть кратким и не превышать 1000 токенов. Если информация объёмная — сожми её, сохранив суть.
Если вопрос не относится к теме ГВС или дома — вежливо откажись отвечать.
ИНСТРУКЦИИ:
- Не выдумывай данные.
- Если информации недостаточно — скажи: "Недостаточно данных".
- Используй Markdown: **жирный** для заголовков, списки для перечислений.
КОНТЕКСТ:
{context}
ВОПРОС:
"{question}"
"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",  
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "deepseek/deepseek-chat-v3.1:free",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 500
                }
            )
            if resp.status_code != 200:
                error_msg = resp.json().get("error", {}).get("message", "Unknown error")
                print(f"OpenRouter error {resp.status_code}: {error_msg}")
                raise HTTPException(status_code=502, detail=f"OpenRouter error: {error_msg}")
            answer = resp.json()["choices"][0]["message"]["content"].strip()
            return {"answer": answer}
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Ошибка генерации ответа")




@app.get("/api/regions/{region_id}/dashboard", response_model=DashboardMetrics)
async def api_get_dashboard(region_id: str, days: int = Query(14, ge=1, le=90), db: AsyncSession = Depends(get_db)):
    if region_id not in REGION_ID_TO_NAME:
        raise HTTPException(status_code=404, detail="Region not found")
    return await get_real_dashboard_metrics(db, region_id, days)


@app.get("/api/regions/{region_id}/houses", response_model=List[HouseListItem])
async def api_get_houses(
    region_id: str,
    status: Optional[str] = Query(None, regex="^(red|yellow|green|in_work)$"),
    incident_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    if region_id not in REGION_ID_TO_NAME:
        raise HTTPException(status_code=404, detail="Region not found")
    return await get_real_house_list(
        db=db,
        region_id=region_id,
        status=status,
        incident_status=incident_status,
        search=search,
    )


@app.get("/api/v2/houses/options")
async def get_houses_options_v2(db: AsyncSession = Depends(get_db)):
    """
    Получить список ВСЕХ домов для создания инцидента (v2).
    Использует lublino_houses_id.
    """
    try:
        # Используем SQLAlchemy для более гибкого запроса, убираем LIMIT
        # или устанавливаем очень большой LIMIT, если担心 слишком большого объема данных
        # можно рассмотреть пагинацию в будущем
        result = await db.execute(
            select(LublinoHousesId.id_house, LublinoHousesId.unom, LublinoHousesId.simple_address)
            # .limit(10000) # Пример увеличения лимита, если нужно ограничить
            .order_by(LublinoHousesId.simple_address, LublinoHousesId.unom) # Сортировка для предсказуемого порядка
        )
        houses = result.fetchall()
        return [
            {
                "id_house": house.id_house,
                "unom": house.unom,
                "simple_address": house.simple_address
            }
            for house in houses
        ]
    except Exception as e:
        print(f"Error getting houses options (v2): {e}")
        # Возвращаем тестовые данные если таблица не существует или произошла другая ошибка
        return [
            {
                "id_house": 1,
                "unom": 12345,
                "simple_address": "ул. Тестовая, д. 1"
            },
            {
                "id_house": 2,
                "unom": 12346,
                "simple_address": "ул. Тестовая, д. 2"
            }
        ]

@app.post("/api/v2/incidents/create")
async def create_incident_v2(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать/обновить инцидент (v2).
    Проверяет существование id_house в lublino_houses_id, получает unom оттуда.
    Добавляет/обновляет в status_houses.
    """
    id_house = payload.get("id_house")
    status_incident = payload.get("status_incident")
    house_health = payload.get("house_health")

    if not all([id_house, status_incident, house_health]):
        raise HTTPException(status_code=400, detail="Missing required fields: id_house, status_incident, house_health")

    try:
        # Проверяем, существует ли id_house в lublino_houses_id
        house_result = await db.execute(
            select(LublinoHousesId.unom, LublinoHousesId.address).where(LublinoHousesId.id_house == id_house)
        )
        house_info = house_result.fetchone()

        if house_info is None:
            # id_house не найден в lublino_houses_id
            raise HTTPException(status_code=404, detail=f"House with id_house {id_house} not found in lublino_houses_id table")

        unom = house_info.unom
        full_address = house_info.address

        # Проверяем, существует ли запись в status_houses
        result = await db.execute(
            select(StatusHealth).where(StatusHealth.id_house == id_house)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Обновляем существующую запись
            existing.status_incident = status_incident
            existing.house_health = house_health
            existing.unom = unom
            print(f"[v2] Updated existing incident for house {id_house}: status={status_incident}, health={house_health}, unom={unom}")
        else:
            # Создаем новую запись
            new_incident = StatusHealth(
                id_house=id_house,
                unom=unom,
                status_incident=status_incident,
                house_health=house_health
            )
            db.add(new_incident)
            print(f"[v2] Created new incident for house {id_house}: status={status_incident}, health={house_health}, unom={unom}")

        await db.commit()
        
        # Отправляем email уведомление если статус проблемный
        if house_health.lower() in ['red', 'yellow']:
            if full_address:
                send_email_notification(
                    house_id=id_house,
                    address=full_address,
                    status=house_health,
                    incident_status=status_incident
                )
            else:
                print(f"Could not get address for house {id_house}, skipping email notification")

        return {"message": "Инцидент (v2) успешно создан или обновлён"}

    except HTTPException:
        # Если это HTTPException (например, 404 выше), пробросим его дальше
        raise
    except Exception as e:
        await db.rollback()
        print(f"Database error in create_incident_v2: {e}") # Логируем ошибку
        raise HTTPException(status_code=500, detail=f"Ошибка (v2) создания инцидента: {str(e)}")


@app.get("/api/houses/options")
async def get_houses_options(db: AsyncSession = Depends(get_db)):
    """Получить список домов для создания инцидента"""
    try:
        # Используем SQL запрос напрямую
        result = await db.execute(text("""
            SELECT id_house, unom, simple_address 
            FROM lublino_houses_id 
            LIMIT 100
        """))
        houses = result.fetchall()
        return [
            {
                "id_house": house.id_house,
                "unom": house.unom,
                "simple_address": house.simple_address
            }
            for house in houses
        ]
    except Exception as e:
        print(f"Error getting houses options: {e}")
        # Возвращаем тестовые данные если таблица не существует
        return [
            {
                "id_house": 1,
                "unom": 12345,
                "simple_address": "ул. Тестовая, д. 1"
            },
            {
                "id_house": 2,
                "unom": 12346,
                "simple_address": "ул. Тестовая, д. 2"
            }
        ]

@app.get("/api/houses/{house_id}", response_model=HouseDetail)
async def api_get_house_detail(house_id: str, db: AsyncSession = Depends(get_db)):
    try:
        data = await get_real_house_detail(db, house_id)
        if not data:
            raise HTTPException(status_code=404, detail="House not found")
        return data
    except Exception as e:
        print(f"Error getting house detail: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/api/houses/{house_id}/status")
async def api_update_house_status(
    house_id: str, 
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Обновить статус дома"""
    try:
        house_id_int = int(house_id)
        
        # Проверяем существование записи
        result = await db.execute(
            text("SELECT id_house, house_health, status_incident FROM status_houses WHERE id_house = :id_house"),
            {"id_house": house_id_int}
        )
        existing = result.fetchone()
        
        if not existing:
            print(f"Запись для дома {house_id_int} не найдена")
            raise HTTPException(status_code=404, detail="House not found")
        
        # Сохраняем старые значения для сравнения
        old_health = existing.house_health
        old_status = existing.status_incident
        
        print(f"Текущее состояние: house_health={existing.house_health}, status_incident={existing.status_incident}")
        
        # Подготовим параметры для обновления
        update_fields = {}
        update_sql_parts = []
        
        # Обработка status_incident
        if 'incident_status' in payload:
            update_sql_parts.append("status_incident = :incident_status")
            update_fields['incident_status'] = payload['incident_status']
            print(f"Обновляем status_incident на: {payload['incident_status']}")
        
        # Обработка house_health
        if 'house_health' in payload:
            update_sql_parts.append("house_health = :house_health")
            update_fields['house_health'] = payload['house_health']
            print(f"Обновляем house_health на: {payload['house_health']}")
        
        if update_sql_parts:
            update_sql = f"UPDATE status_houses SET {', '.join(update_sql_parts)} WHERE id_house = :id_house"
            update_fields['id_house'] = house_id_int
            
            print(f"Выполняем SQL: {update_sql} с параметрами: {update_fields}")
            
            result = await db.execute(text(update_sql), update_fields)
            print(f"Обновлено строк: {result.rowcount}")
            await db.commit()
        
        # Проверим, что данные действительно обновились
        check_result = await db.execute(
            text("SELECT house_health, status_incident FROM status_houses WHERE id_house = :id_house"),
            {"id_house": house_id_int}
        )
        updated = check_result.fetchone()
        print(f"После обновления: house_health={updated.house_health}, status_incident={updated.status_incident}")
        
        # Отправляем email уведомление если статус стал проблемным (только если изменился)
        if (updated.house_health and updated.house_health.lower() in ['red', 'yellow'] and 
            (old_health != updated.house_health or old_status != updated.status_incident)):
            
            # Получаем полный адрес из lublino_houses_id
            address_result = await db.execute(
                text("SELECT address FROM lublino_houses_id WHERE id_house = :id_house"),
                {"id_house": house_id_int}
            )
            full_address = address_result.scalar_one_or_none()
            
            if full_address:
                send_email_notification(
                    house_id=house_id_int,
                    address=full_address,
                    status=updated.house_health,
                    incident_status=updated.status_incident
                )
            else:
                print(f"Could not get address for house {house_id_int}, skipping email notification")
        
        return {
            "ok": True, 
            "message": "Status updated successfully",
            "updated_data": {
                "house_health": updated.house_health,
                "status_incident": updated.status_incident
            }
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid house_id format")
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")

@app.get("/api/houses/{house_id}/status-detail")
async def api_get_house_status_detail(house_id: str, db: AsyncSession = Depends(get_db)):
    """Получить детали статуса дома из таблицы status_houses"""
    try:
        # Получаем статус из таблицы status_houses
        result = await db.execute(
            text("""
                SELECT id_house, unom, house_health, status_incident 
                FROM status_houses 
                WHERE id_house = :house_id
            """),
            {"house_id": int(house_id)}
        )
        status_info = result.fetchone()
        if not status_info:
            raise HTTPException(status_code=404, detail="House status not found")

        # Маппинг для преобразования house_health в ваш внутренний формат
        health_reverse_mapping = {
            'Red': 'red',
            'Yellow': 'yellow',
            'Green': 'green'
        }
        # Маппинг для преобразования status_incident в русский
        status_reverse_mapping = {
            'New': 'Новый',
            'Work': 'В работе',
            'Repair': 'В ремонте',
            'Resolved': 'Решен',
            'None': 'Статус не задан'
        }

        # Получаем базовую информацию из основной таблицы
        house_result = await db.execute(
            text("""
                SELECT simple_address, address, nreg, unom, n_fias
                FROM lublino_houses_id 
                WHERE id_house = :house_id
            """),
            {"house_id": int(house_id)}
        )
        house_info = house_result.fetchone()

        # Формируем ответ в формате HouseDetail
        response_data = {
            "house_id": str(status_info.id_house),
            "address": house_info.address if house_info else "",
            "simple_address": house_info.simple_address if house_info else "",
            "region": "lublino",
            "status": health_reverse_mapping.get(status_info.house_health, 'green'),
            "incident_status": status_reverse_mapping.get(status_info.status_incident, 'Новый'),
            "fias": house_info.n_fias,
            "unom": house_info.unom, 
            "nreg": house_info.nreg,
        }
        return response_data

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid house_id format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    



@app.get("/api/regions/{region_id}/llm-context")
async def api_llm_context(region_id: str, db: AsyncSession = Depends(get_db)):
    if region_id not in REGION_ID_TO_NAME:
        raise HTTPException(status_code=404, detail="Region not found")
    return await get_real_llm_context(db, region_id)


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/db-health")
async def db_health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )


@app.get("/api/model-relearn/history")
async def get_model_history(db: AsyncSession = Depends(get_db)):
    """Получить историю обучения моделей"""
    try:
        # Получаем все записи из таблицы
        result = await db.execute(text("SELECT date_relearn, model_name, status_relearn FROM model_relearn ORDER BY date_relearn DESC"))
        records = result.fetchall()
        return [
            {
                "id": i,  # Используем индекс как id
                "date": record.date_relearn.isoformat() if record.date_relearn else None,
                "model_name": record.model_name,
                "status_relearn": record.status_relearn
            }
            for i, record in enumerate(records)
        ]
    except Exception as e:
        print(f"Error getting model history: {e}")
        # Если таблица не существует, возвращаем пустой список
        return []

@app.post("/api/model-relearn/start")
async def start_model_retraining(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Запустить переобучение модели"""
    try:
        model_name = payload.get("model_name", f"model_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        status_relearn = payload.get("status_relearn", "started")
        current_date = datetime.now()
        
        # Создаем запись напрямую через SQL
        await db.execute(text("""
            INSERT INTO model_relearn (model_name, status_relearn, date_relearn) 
            VALUES (:model_name, :status_relearn, :date_relearn)
        """), {
            "model_name": model_name, 
            "status_relearn": status_relearn,
            "date_relearn": current_date
        })
        await db.commit()
        return {"message": "Переобучение модели запущено"}
    except Exception as e:
        print(f"Error starting model retraining: {e}")
        return {"message": f"Ошибка: {str(e)}"}


@app.get("/api/forecast-overall")
async def get_forecast_overall(db: AsyncSession = Depends(get_db)):
    """Получить общий прогноз из таблицы forecast_overall"""
    try:
        # Query the forecast_overall table (no region_id needed)
        result = await db.execute(
            text("SELECT v1, v2 FROM forecast_overall LIMIT 1")
        )
        row = result.fetchone()
        
        if row:
            return {"v1": row.v1, "v2": row.v2}
        else:
            # Return default values if no data found
            return {"v1": 0.0, "v2": 0.0}
    except Exception as e:
        print(f"Error fetching forecast data: {e}")
        raise HTTPException(status_code=500, detail="Error fetching forecast data")