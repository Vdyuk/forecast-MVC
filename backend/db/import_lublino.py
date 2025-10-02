import os
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv
from pathlib import Path
import asyncio

# Загружаем переменные окружения
load_dotenv()

# Подключение к БД
DATABASE_URL = (
    f"postgresql+asyncpg://"
    f"{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

async def import_lublino_from_csv(csv_path: str):
    engine = create_async_engine(DATABASE_URL, echo=True)

    # 1. Чтение CSV
    try:
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='cp1251',
            on_bad_lines='skip'
        )
    except UnicodeDecodeError:
        # fallback на UTF-8
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='utf-8',
            on_bad_lines='skip'
        )

    # 2. Фильтрация по району "Люблино"
    df = df[df['DISTRICT'].str.contains('Люблино', case=False, na=False, regex=False)].copy()

    # 3. Выбор нужных столбцов
    required_columns = [
        'UNOM', 'ADDRESS', 'SIMPLE_ADDRESS', 'DISTRICT',
        'N_FIAS', 'D_FIAS', 'NREG', 'TDOC', 'NDOC', 'DDOC',
        'SOSTAD', 'STATUS', 'DREG', 'KLADR', 'P90', 'P91'
    ]

    missing_cols = set(required_columns) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Отсутствуют столбцы в CSV: {missing_cols}")

    df = df[required_columns]

    # 4. Преобразуем NaN в None
    df = df.where(pd.notnull(df), None)

    # 5. Создание таблицы
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS lublino_houses (
        unom BIGINT,
        address TEXT,
        simple_address TEXT,
        district TEXT,
        n_fias UUID,
        d_fias DATE,
        nreg TEXT,
        tdoc TEXT,
        ndoc TEXT,
        ddoc DATE,
        sostad TEXT,
        status TEXT,
        dreg DATE,
        kladr TEXT,
        p90 TEXT,
        p91 TEXT
    );
    """

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS lublino_houses;"))
        await conn.execute(text(create_table_sql))

        # 6. Подготовка записей с приведением типов
        records = df.to_dict(orient='records')
        cleaned_records = []

        for r in records:
            # UNOM → int
            if r['UNOM'] is not None:
                try:
                    r['UNOM'] = int(float(r['UNOM']))
                except (ValueError, TypeError, OverflowError):
                    r['UNOM'] = None

            # NREG → str (без .0)
            if r['NREG'] is not None:
                try:
                    r['NREG'] = str(int(float(r['NREG'])))
                except (ValueError, TypeError):
                    r['NREG'] = str(r['NREG'])

            # KLADR → str (без экспоненты и .0)
            if r['KLADR'] is not None:
                try:
                    val = float(r['KLADR'])
                    if val.is_integer():
                        r['KLADR'] = str(int(val))
                    else:
                        r['KLADR'] = str(int(round(val)))
                except (ValueError, TypeError, OverflowError):
                    r['KLADR'] = str(r['KLADR'])

            # Даты → 'YYYY-MM-DD'
            for col in ['D_FIAS', 'DDOC', 'DREG']:
                if r[col] is not None:
                    try:
                        r[col] = pd.to_datetime(r[col], dayfirst=True).date()
                    except Exception:
                        r[col] = None

            cleaned_records.append(r)

        # 7. Вставка
        await conn.execute(
            text("""
                INSERT INTO lublino_houses (
                    unom, address, simple_address, district,
                    n_fias, d_fias, nreg, tdoc, ndoc, ddoc,
                    sostad, status, dreg, kladr, p90, p91
                ) VALUES (
                    :UNOM, :ADDRESS, :SIMPLE_ADDRESS, :DISTRICT,
                    :N_FIAS, :D_FIAS, :NREG, :TDOC, :NDOC, :DDOC,
                    :SOSTAD, :STATUS, :DREG, :KLADR, :P90, :P91
                )
            """),
            cleaned_records
        )

    print(f"✅ Успешно загружено {len(cleaned_records)} записей в таблицу 'lublino_houses'")

if __name__ == "__main__":
    import asyncio

    csv_file = "data-60562-2025-09-26.csv"  
    asyncio.run(import_lublino_from_csv(csv_file))