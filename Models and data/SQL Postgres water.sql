select *
from lublino_houses lh 
limit 20

select count(unom), count(distinct unom)
from lublino_houses lh 

select *
from water_consump
where id_house = 295
		and cast(time_5min as date) = '2025-09-01'

select count(distinct id_house)
from water_consump


select 
ROW_NUMBER() OVER (ORDER BY RANDOM()) as id_house
,unom,address,simple_address, district,n_fias,nreg
from lublino_houses lh

CREATE TABLE lublino_houses_id AS
SELECT 
ROW_NUMBER() OVER (ORDER BY RANDOM()) as id_house
,unom,address,simple_address, district,n_fias,nreg
from lublino_houses lh;

select count(*), count(distinct id_house), count(distinct unom)  from lublino_houses_id

select * from lublino_houses_id




/****	холодная и горячая *****/
select *
from water_consump_hot
limit 20

/****************** разница хол и горячей *******************/
create table water_diffr_coldhot as (
select
	id_house
	,time_5min
	,water_consumption - water_hot as diffr_cldht
	,case when water_consumption > 0.01 
			then (water_consumption - water_hot)/water_consumption
		 else 0
	end as diffr_ratio
from water_consump_hot
);

select *
from public.water_diffr_coldhot
limit 20


/****	сбой - линейный тренд *****/
select *
from public.water_lintrend_3000
limit 20


/*** вставляем кейс с линейным трендом в таблицы с графиками и не забыть с адресами ****/

/*  список столбцов таблицы для копирования  */
SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
FROM information_schema.columns 
WHERE table_name = 'water_consump_hot';

DELETE FROM water_consump_hot 
WHERE id_house = 3000;

INSERT INTO water_consump_hot (id_house, time_5min, water_consumption, water_hot)
SELECT id_house, time_5min, water_consumption, water_hot
FROM water_lintrend_3000
;

select *
from water_consump_hot
where id_house = 3000
limit 30

/*  список столбцов таблицы для копирования  */
SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
FROM information_schema.columns 
WHERE table_name = 'water_diffr_coldhot';

DELETE FROM water_diffr_coldhot 
WHERE id_house = 3000;

INSERT INTO water_diffr_coldhot (id_house, time_5min, diffr_cldht, diffr_ratio)
SELECT 	id_house
	,time_5min
	,water_consumption - water_hot as diffr_cldht
	,case when water_consumption > 0.01 
			then (water_consumption - water_hot)/water_consumption
		 else 0
	end as diffr_ratio
FROM water_consump_hot
where id_house = 3000
;

select *
from public.water_diffr_coldhot
where id_house = 3000
	and time_5min between '2025-09-28 00:00:00' and '2025-10-03 00:00:00'


/*  список столбцов таблицы для копирования  */
SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
FROM information_schema.columns 
WHERE table_name = 'lublino_houses_id';

INSERT INTO lublino_houses_id (id_house, unom, address, simple_address, district, n_fias, nreg)
SELECT 3000, unom, address, simple_address, district, n_fias, nreg
FROM lublino_houses_id
where id_house = 828
;

select *
from lublino_houses_id
where id_house = 3000
;

UPDATE lublino_houses_id 
set
address = 'Российская Федерация, город Москва, внутригородская территория муниципальный округ Люблино, 1-й Тестовый проезд, дом 1'
, simple_address = '1-й Тестовый проезд, дом 1'
where id_house = 3000;

select *
from lublino_houses_id
where id_house = 3000
;

/****************  Данные по часам   **********************/

drop table water_consump_hot_1h;

create table water_consump_hot_1h as (
select
	id_house,
    date_trunc('hour', time_5min) as time_1hour,
    SUM(water_consumption ) as water_cold,
    SUM(water_hot) as water_hot
FROM water_consump_hot
GROUP BY id_house, date_trunc('hour', time_5min)
)
;

select *
from water_consump_hot_1h
where id_house = 3000
limit 20


drop table water_diffr_coldhot_1h;

create table water_diffr_coldhot_1h as (
select
	id_house
	,time_1hour
	,water_cold - water_hot as diffr_cldht
	,case when water_cold > 0.05 
			then (water_cold - water_hot)/water_cold
		 else 0
	end as diffr_ratio
from water_consump_hot_1h
);

select *
from water_diffr_coldhot_1h
where id_house = 3000
limit 20



/*** Второй сбой аномалия: иногда резкие всплески по холодной воде ****/

DELETE FROM water_consump_hot 
WHERE id_house = 3001;

INSERT INTO water_consump_hot (id_house, time_5min, water_consumption, water_hot)
SELECT id_house, time_5min, water_consumption, water_hot
FROM public.wtr_jump_3001
;

select *
from water_consump_hot
where id_house = 3001
limit 30

DELETE FROM water_diffr_coldhot 
WHERE id_house = 3001;

INSERT INTO water_diffr_coldhot (id_house, time_5min, diffr_cldht, diffr_ratio)
SELECT 	id_house
	,time_5min
	,water_consumption - water_hot as diffr_cldht
	,case when water_consumption > 0.01 
			then (water_consumption - water_hot)/water_consumption
		 else 0
	end as diffr_ratio
FROM water_consump_hot
where id_house = 3001
;

select *
from public.water_diffr_coldhot
where id_house = 3001
	and time_5min between '2025-09-28 00:00:00' and '2025-10-03 00:00:00'



INSERT INTO lublino_houses_id (id_house, unom, address, simple_address, district, n_fias, nreg)
SELECT 3001, unom, address, simple_address, district, n_fias, nreg
FROM lublino_houses_id
where id_house = 189
;

select *
from lublino_houses_id
where id_house = 3001
;

UPDATE lublino_houses_id 
set
address = 'Российская Федерация, город Москва, внутригородская территория муниципальный округ Люблино, 1-й Тестовый проезд, дом 2'
, simple_address = '1-й Тестовый проезд, дом 2'
where id_house = 3001;

select *
from lublino_houses_id
where id_house = 3001
;

/**************** по часам для 3001  **********************/

insert into water_consump_hot_1h
select
	id_house,
    date_trunc('hour', time_5min) as time_1hour,
    SUM(water_consumption ) as water_cold,
    SUM(water_hot) as water_hot
FROM water_consump_hot
where id_house = 3001
GROUP BY id_house, date_trunc('hour', time_5min)
;

select *
from water_consump_hot_1h
where id_house = 3001
limit 20


insert into water_diffr_coldhot_1h 
select
	id_house
	,time_1hour
	,water_cold - water_hot as diffr_cldht
	,case when water_cold > 0.05 
			then (water_cold - water_hot)/water_cold
		 else 0
	end as diffr_ratio
from water_consump_hot_1h
where id_house = 3001
;

select *
from water_diffr_coldhot_1h
where id_house = 3001
limit 20

SELECT NOW();
SELECT LOCALTIMESTAMP;


/*** вставляем кейс 3002 с пропущенными значениями ****/

DELETE FROM water_consump_hot 
WHERE id_house = 3002;

INSERT INTO water_consump_hot (id_house, time_5min, water_consumption, water_hot)
SELECT id_house, time_5min, water_consumption, water_hot
FROM public.wtr_blank_3002
;

/** посмотрим пустые в ровный час **/
SELECT *
FROM water_consump_hot
WHERE id_house = 3002
AND time_5min BETWEEN '2025-09-29 08:00:00.000' AND '2025-09-30 23:00:00.000'
AND EXTRACT(MINUTE FROM time_5min) = 0
ORDER BY time_5min;



DELETE FROM water_diffr_coldhot 
WHERE id_house = 3002;

INSERT INTO water_diffr_coldhot (id_house, time_5min, diffr_cldht, diffr_ratio)
SELECT 	id_house
	,time_5min
	,coalesce(water_consumption,0) - coalesce(water_hot,0) as diffr_cldht
	,case when water_consumption > 0.01 
			then (water_consumption - water_hot)/water_consumption
		  when water_consumption is null
		  	then 0.1
		 else 0
	end as diffr_ratio
FROM water_consump_hot
where id_house = 3002
;

select *
from public.water_diffr_coldhot
where id_house = 3002
	and time_5min between '2025-09-30 22:00:00.000' and '2025-09-30 22:30:00.000'




INSERT INTO lublino_houses_id (id_house, unom, address, simple_address, district, n_fias, nreg)
SELECT 3002, unom, address, simple_address, district, n_fias, nreg
FROM lublino_houses_id
where id_house = 1662
;

select *
from lublino_houses_id
where id_house = 3002
;

UPDATE lublino_houses_id 
set
address = 'Российская Федерация, город Москва, внутригородская территория муниципальный округ Люблино, 1-й Тестовый проезд, дом 3'
, simple_address = '1-й Тестовый проезд, дом 3'
where id_house = 3002;

select *
from lublino_houses_id
where id_house = 3002
;

/**** по часам для 3002 - нельзя суммировать из 5-мин, т.к. есть пропущенные **********/
/**** будем считать, что потребление за час - это разность между показаниями счетчика на конец и начало периода, а не сумма 5-минуток ****/

DELETE FROM water_consump_hot_1h 
WHERE id_house = 3002;

insert into water_consump_hot_1h
select
	3002 as id_house,
    date_trunc('hour', time_5min) as time_1hour,
    SUM(water_consumption ) as water_cold,
    SUM(water_hot) as water_hot
FROM water_consump_hot
where id_house = 1662
GROUP BY id_house, date_trunc('hour', time_5min)
;

/** Update пустых значений в ровный час для 3002 **/
UPDATE water_consump_hot_1h t
SET 
    water_cold = s.water_consumption,
    water_hot = s.water_hot
FROM water_consump_hot s
WHERE t.id_house = 3002 and s.id_house = 3002
	and t.time_1hour = s.time_5min
;

select *
from water_consump_hot_1h
where id_house = 3002
	and time_1hour between '2025-09-30 08:00:00.000' and '2025-09-30 23:00:00.000'



DELETE FROM water_diffr_coldhot_1h 
WHERE id_house = 3002;

insert into water_diffr_coldhot_1h 
select
	id_house
	,time_1hour
	,water_cold - water_hot as diffr_cldht
	,case when water_cold > 0.05 
			then (water_cold - water_hot)/water_cold
		  when water_cold is null
		  	then 0.1
		 else 0
	end as diffr_ratio
from water_consump_hot_1h
where id_house = 3002
;

select *
from water_diffr_coldhot_1h
where id_house = 3002
	and time_1hour between '2025-09-30 08:00:00.000' and '2025-09-30 23:00:00.000'


	
	
	
	
	
/*** вставляем кейс 3003 - биение около константы  ****/

DELETE FROM water_consump_hot 
WHERE id_house = 3003;

INSERT INTO water_consump_hot (id_house, time_5min, water_consumption, water_hot)
SELECT id_house, time_5min, water_consumption, water_hot
FROM public.wtr_const_3003
;

select *
from water_consump_hot
where id_house = 3003
limit 30

DELETE FROM water_diffr_coldhot 
WHERE id_house = 3003;

INSERT INTO water_diffr_coldhot (id_house, time_5min, diffr_cldht, diffr_ratio)
SELECT 	id_house
	,time_5min
	,coalesce(water_consumption,0) - coalesce(water_hot,0) as diffr_cldht
	,case when water_consumption > 0.01 
			then (water_consumption - water_hot)/water_consumption
		  when water_consumption is null
		  	then 0.1
		 else 0
	end as diffr_ratio
FROM water_consump_hot
where id_house = 3003
;


select *
from public.water_diffr_coldhot
where id_house = 3003
	and time_5min between '2025-09-28 00:00:00' and '2025-10-03 00:00:00'



INSERT INTO lublino_houses_id (id_house, unom, address, simple_address, district, n_fias, nreg)
SELECT 3003, unom, address, simple_address, district, n_fias, nreg
FROM lublino_houses_id
where id_house = 1513
;

select *
from lublino_houses_id
where id_house = 3003
;

public.public.lublino_houses_id

UPDATE lublino_houses_id 
set
address = 'Российская Федерация, город Москва, внутригородская территория муниципальный округ Люблино, 1-й Тестовый проезд, дом 4'
, simple_address = '1-й Тестовый проезд, дом 4'
where id_house = 3003;

select *
from lublino_houses_id
where id_house = 3003
;



select *
from public.status_health






drop table incident_hist_1

/***********  Создание истории инцидентов  *********************/
create table incident_hist_1 as (
select *
from (
select *
	,lag(fl_incident_1h)  over(partition by id_house ORDER BY time_5min)
			as prev_fl_incident_1h
from (
select
	id_house
	,time_5min
	,water_consumption
	,water_hot
	,diffr_prcnt_5min
	,fl_incident_5min
	,sum(fl_incident_5min) over(partition by id_house ORDER BY time_5min
									ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
			as cnt_incident_5min_1h
	,water_col_1h
	,water_hot_1h
	,diffr_water_1h
	,diffr_prcnt_1h
	,fl_incident_1h
from (
select
	id_house
	,time_5min
	,water_consumption
	,water_hot
	,case when water_consumption > 0.01
		  then abs(water_consumption - water_hot)/water_consumption
		  else 0
		end as diffr_prcnt_5min
	,case when water_consumption > 0.01
		  and abs(water_consumption - water_hot)/water_consumption > 0.1
		  then 1
		  else 0
		end as fl_incident_5min
	,water_col_1h
	,water_hot_1h
	,abs(water_col_1h - water_hot_1h) as diffr_water_1h
	,case when water_col_1h > 0.05 
		  then abs(water_col_1h - water_hot_1h)/water_col_1h
		  else 0
		end as diffr_prcnt_1h
	,case when water_col_1h > 0.05 
		  and abs(water_col_1h - water_hot_1h)/water_col_1h >0.1
		  then 1
		  else 0
		end as fl_incident_1h

from (
	select
	id_house
	,time_5min
	,water_consumption
	,water_hot
	,sum(water_consumption) over(partition by id_house order by time_5min
								rows between 11 preceding and CURRENT ROW)
		as water_col_1h
		
	,sum(water_hot) over(partition by id_house order by time_5min
								rows between 11 preceding and CURRENT ROW)
		as water_hot_1h
	from water_consump_hot
	where time_5min between '2025-09-01 00:00:00.000' AND '2025-10-05 23:55:00.000'
	) a
) a
) a
) a
where fl_incident_5min =1 or fl_incident_1h = 1
	or (fl_incident_1h = 0 and prev_fl_incident_1h =1)
)
;




select count(*) from incident_hist_1

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_1
where id_house = 2126
order by time_5min desc

select *
from incident_hist_1
where id_house = 108

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_1
where id_house = 1845
order by time_5min desc


select *
from water_consump_hot
where id_house = 3001
	and time_5min between '2025-09-27 00:00:00.000' AND '2025-09-29 00:00:00.000'



	
create table incident_hist_2 as (
select *
from (
select
id_house
,time_5min
,diffr_prcnt_1h
,case when fl_incident_1h =1 and coalesce(prev_fl_incident_1h,0) =0
		then 1
	  when fl_incident_1h = 0 and prev_fl_incident_1h=1
	  	then 2
	  when fl_incident_5min =1 and prev_fl_incident_5min = 0
	  	then 3
  end as type_incdnt
,case when fl_incident_1h =1 and coalesce(prev_fl_incident_1h,0) =0
		then 'Инцидент: отклонение ХВС-ГВС за 1 час на'||to_char(diffr_prcnt_1h * 100, '999%')
	  when fl_incident_1h = 0 and prev_fl_incident_1h=1
	  	then 'Отклонения за 1 час нет'
	  when fl_incident_5min =1 and prev_fl_incident_5min = 0
	  	then 'Предупреждение: отклонение ХВС-ГВС за 5 мин'
  end as comment_incdnt
from (
	select 
	id_house
	,time_5min
	,diffr_prcnt_1h
	,fl_incident_1h
	,fl_incident_5min
	,prev_fl_incident_1h
	,lag(fl_incident_5min) over(partition by id_house  order by time_5min)
			as prev_fl_incident_5min
	from incident_hist_1
	)	a
) a
where type_incdnt is not null
);

select count(id_house), count(distinct id_house)
from incident_hist_2

select distinct id_house
from incident_hist_2

select count(*) from incident_hist_2
where id_house = 3001

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_2
where id_house = 3001
order by time_5min desc

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_2
where id_house = 2126
order by time_5min desc

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_2
where id_house = 1845
order by time_5min desc

SELECT 
    to_char(time_5min, 'DD/MM HH24:MI') as time_minute_text,
    *
FROM incident_hist_2
where id_house = 1418
order by time_5min desc


/********** НОВАЯ таблица со статусами	*************/


CREATE TABLE status_houses AS
WITH warning_3 as (
select
	id_house
	,count(1) as cnt_warn_type3
FROM incident_hist_2
WHERE time_5min BETWEEN NOW() - INTERVAL '24 hours' AND NOW()
	and type_incdnt = 3
group by id_house
),

critical_1 as (
select
	id_house
	,count(1) as cnt_warn_type1
FROM incident_hist_2
WHERE time_5min BETWEEN NOW() - INTERVAL '24 hours' AND NOW()
	and type_incdnt = 1
group by id_house
),

warning_12 as (
select
	id_house
	,max(case when type_incdnt = 2 then time_5min
		end) as last_time_incdnt_2
	,max(case when type_incdnt = 1 then time_5min
		end) as last_time_incdnt_1
FROM incident_hist_2
WHERE time_5min BETWEEN NOW() - INTERVAL '120 hours' AND NOW()
	and type_incdnt in (1,2)
group by id_house
)

select
	allhs.id_house 
	,allhs.unom
	,case when w_12.last_time_incdnt_1 > w_12.last_time_incdnt_2
			then 'Red'
		  when w_12.last_time_incdnt_2 is null and w_12.last_time_incdnt_1 is not null
			then 'Red'
		 /* если за 24ч доля часовых инцидентов больше 10%, то желтый свет */
		  when cr1.cnt_warn_type1 >=3
		  	then 'Yellow'
		 /* если за 24ч доля предупреждений 5-минуток больше 10%, то желтый свет */
		  when w_3.cnt_warn_type3 >=29
		  	then 'Yellow'
		 when w_12.last_time_incdnt_2 > w_12.last_time_incdnt_1
			then 'Green' 	
		  	
		  else 'Green'
		end as  House_health
	,cast(null as varchar(50)) as Status_incident
	
from lublino_houses_id as allhs
	left join warning_3 as w_3
		on w_3.id_house = allhs.id_house 
	left join warning_12 as w_12
		on w_12.id_house = allhs.id_house
	left join critical_1 as cr1
		on cr1.id_house = allhs.id_house
;	


select count() from status_houses

select
House_health, count(*)
from status_houses
group by House_health

select
*
from status_houses
where House_health in ('Red','Yellow')

/* Заполнение Status_incident */
UPDATE status_houses 
SET Status_incident = 
		CASE 
	        WHEN random() < 0.1
	        	 then 'New'
	        WHEN random() < 0.6
	        	 then 'Repair'
	        else 'Work'
	        end
where House_health in ('Red','Yellow');

select *
from status_houses
where House_health in ('Red','Yellow')


select 
*
from incident_hist_2 
where id_house = 108

select
	*
FROM incident_hist_1
where id_house = 108


/****** Текущие статус инцидентов и работы */

create table status_current_work (
    stts_name varchar(50),  cnt INT
);

INSERT INTO status_current_work (stts_name, cnt)
VALUES 
    ('Новый', 1),
    ('В работе', 2),
    ('Ремонт объекта', 5),
    ('Устранено', 8)
  ;

select * from status_current_work



/********** СТАРАЯ таблица статусов	*************/
create table status_health as 
select
	id_house,
	unom,
	case when random() >= 0.995 then 'Red'
		 when random() >= 0.99 then 'Yellow'
		 else 'Green'
	end as House_health,
	cast(null as varchar(50)) as Status_incident
from lublino_houses_id;

select 
House_health
,count(1) as cnt
from status_health
group by House_health

UPDATE status_health 
SET Status_incident = 
		CASE 
	        WHEN random() < 0.2
	        	 then 'New'
	        WHEN random() < 0.6
	        	 then 'Repair'
	        else 'Work'
	        end
where House_health in ('Red','Yellow');

UPDATE status_health 
SET Status_incident = 
		CASE 
	        WHEN random() < 0.05
	        	 then 'Resolved'
	        else Null
	        end
where House_health = 'Green';

select 
Status_incident
,House_health
,count(1) as cnt
from status_health
group by Status_incident,House_health

select *
from status_health
limit 30




/*****  Диаграмма по кол-ву инцидентов по дням  *****/

CREATE TABLE daily_incidents AS
WITH dates AS (
    SELECT 
        CURRENT_DATE - (n || ' days')::interval as incident_date
    FROM GENERATE_SERIES(1, 30) as n  -- начинаем с 1, а не с 0
),
incident_types AS (
    SELECT 'critical' as incident_type
    UNION ALL SELECT 'warning'
)
SELECT 
    d.incident_date,
    it.incident_type,
    FLOOR(RANDOM() * 9 + 1)::int as incident_count
FROM dates d
CROSS JOIN incident_types it
ORDER BY d.incident_date DESC, it.incident_type;


insert into daily_incidents (incident_date, incident_type, incident_count)
select
cast(CURRENT_DATE as timestamp), 'critical' as incident_type, count(1) as incident_count
from status_houses
where House_health = 'Red'
;

insert into daily_incidents (incident_date, incident_type, incident_count)
select
cast(CURRENT_DATE as timestamp), 'warning' as incident_type, count(1) as incident_count
from status_houses
where House_health = 'Yellow'
;


select * from daily_incidents;




/***** таблица для общего прогноза ***/
create table forecast_overall (v1 real, v2 real, v3 real, v4 real, v5 real, v6 INT, v7 INT, v8 INT, v9 varchar(100), v10 varchar(100), v11 varchar(100));

insert into forecast_overall (v1, v2)
values(2.3, 15)

select *
from forecast_overall


create table model_relearn (
    model_name varchar(50),
    date_relearn DATE, 
    status_relearn varchar(20)
);
INSERT INTO model_relearn (model_name, date_relearn, status_relearn)
VALUES 
    ('GARCH_5min', '2025-09-03', 'success'),
    ('GARCH_5min', '2025-09-10', 'success'),
    ('GARCH_5min', '2025-09-17', 'success'),
    ('GARCH_5min', '2025-09-24', 'success'),  
    ('GARCH_5min', '2025-10-01', 'success'), 
    ('ARIMA_1h', '2025-09-03', 'success'),
    ('ARIMA_1h', '2025-09-10', 'success'),
    ('ARIMA_1h', '2025-09-17', 'success'),
    ('ARIMA_1h', '2025-09-24', 'success'),
    ('ARIMA_1h', '2025-10-01', 'success')
  ;

select * from model_relearn



/***** детальный прогноз по 5-мин и всем домам ***/

select *
from public.water_forecast_all
limit 20

select count(distinct id_house)
from public.water_forecast_all

select *
from public.water_forecast_all
where id_house = 3000
limit 20


	/**** долгосрочный прогноз по аномальным домам  ***/
/*  список столбцов таблицы для копирования  */
SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
FROM information_schema.columns 
WHERE table_name = 'water_forecast_all';

insert into water_forecast_all (id_house, ds, yhat, yhat_lower, yhat_upper)
select 3000, ds, yhat, yhat_lower, yhat_upper
from water_forecast_all
where id_house = 828
;

insert into water_forecast_all (id_house, ds, yhat, yhat_lower, yhat_upper)
select 3001, ds, yhat, yhat_lower, yhat_upper
from water_forecast_all
where id_house = 189
;

insert into water_forecast_all (id_house, ds, yhat, yhat_lower, yhat_upper)
select 3002, ds, yhat, yhat_lower, yhat_upper
from water_forecast_all
where id_house = 1662
;

insert into water_forecast_all (id_house, ds, yhat, yhat_lower, yhat_upper)
select 3003, ds, yhat, yhat_lower, yhat_upper
from water_forecast_all
where id_house = 1513
;

select id_house, count(*)
from water_forecast_all
where id_house between 3000 and 3303
group by id_house
;


/****************** разница между моделью и хол*******************/
create table diffr_model_cold_5min as (
select
	f1.id_house
	,f1.ds
	,f1.yhat
	,w1.water_consumption
	,w1.water_consumption - f1.yhat as diffr_cold_mdl
	,case when f1.yhat > 0.01 
			then abs(w1.water_consumption - f1.yhat)/f1.yhat
		 else 0
	end as diffr_ratio_5min
from water_consump_hot as w1
	inner join water_forecast_all as f1
		on f1.id_house = w1.id_house
		and f1.ds = w1.time_5min
where w1.time_5min between '2025-10-02 00:00:00' and '2025-10-08 00:00:00'
	 and f1.ds between '2025-10-02 00:00:00' and '2025-10-08 00:00:00'

)
;

select count(*), min(ds), max(ds) from diffr_model_cold_5min

select *
from water_consump_hot as w1
where w1.time_5min between '2025-10-02 00:00:00' and '2025-10-02 00:05:00'
limit 10

select *
from water_forecast_all as w1
where w1.ds between '2025-10-02 00:00:00' and '2025-10-02 00:05:00'
limit 10



create table diffr_model_cold_5min_2 as (
select 
id_house
,ds
,yhat
,water_consumption
,diffr_cold_mdl
,diffr_ratio_5min
	/* показатели за прошедшие 24 часа */
,sum(yhat) over(partition by id_house order by ds 
			rows between 287 preceding and current row)
			as sum_model_prev_24h
,sum(diffr_cold_mdl) over(partition by id_house order by ds
			rows between 287 preceding and current row)
			as sum_diffr_prev_24h
,sum(abs(diffr_cold_mdl)) over(partition by id_house order by ds
			rows between 287 preceding and current row)
			as sum_abs_diffr_prev_24h
,sum(water_consumption) over(partition by id_house order by ds 
			rows between 287 preceding and current row)
			as sum_cold_prev_24h
			
	/* прогноз за следующие 24 часа */		
,sum(yhat) over(partition by id_house order by ds 
			rows between current row and 288 following)
			as sum_model_next_24h
,sum(diffr_cold_mdl) over(partition by id_house order by ds
			rows between current row and 288 following)
			as sum_diffr_next_24h
,sum(abs(diffr_cold_mdl)) over(partition by id_house order by ds
			rows between current row and 288 following)
			as sum_abs_diffr_next_24h
,sum(water_consumption) over(partition by id_house order by ds 
			rows between current row and 288 following)
			as sum_cold_next_24h
			
	/* прогноз за следующие 24-48ч часов */		
,sum(yhat) over(partition by id_house order by ds 
			rows between 289 following and 576 following)
			as sum_model_next2_24h
,sum(diffr_cold_mdl) over(partition by id_house order by ds
			rows between 289 following and 576 following)
			as sum_diffr_next2_24h
,sum(abs(diffr_cold_mdl)) over(partition by id_house order by ds
			rows between 289 following and 576 following)
			as sum_abs_diffr_next2_24h
,sum(water_consumption) over(partition by id_house order by ds 
			rows between 289 following and 576 following)
			as sum_cold_next2_24h
			
,sum(case when diffr_ratio_5min > 0.1 then 1 end ) over(partition by id_house order by ds 
			rows between 287 preceding and current row)
			as cnt_difr10_prev24h
,sum(case when diffr_ratio_5min > 0.1 then 1 end ) over(partition by id_house order by ds 
			rows between current row and 288 following)
			as cnt_difr10_next24h
,sum(case when diffr_ratio_5min > 0.1 then 1 end ) over(partition by id_house order by ds 
			rows between 289 following and 576 following)
			as cnt_difr10_next2_24h
from diffr_model_cold_5min
)
;

select
*
from diffr_model_cold_5min_2
limit 20

select
avg(sum_model_prev_24h - sum_cold_prev_24h) as avg_sum_sum_prev
,STDDEV(sum_model_prev_24h - sum_cold_prev_24h) as std_sum_sum_prev
,avg(sum_diffr_prev_24h) as avg_sum_diffr_prev_24h
,STDDEV(sum_diffr_prev_24h) as std_sum_diffr_prev_24h
,avg(sum_abs_diffr_prev_24h) as avg_sum_abs_diffr_prev_24h
,STDDEV(sum_abs_diffr_prev_24h) as std_sum_abs_diffr_prev_24h
from diffr_model_cold_5min_2
where ds = '2025-10-03 08:15:00.000'
and id_house < 3000

если разность sum_model_prev_24h - sum_cold_prev_24h меньше 0.77*3=2.31, то в рамках нормы

sum_model_next2_24h - sum_cold_next2_24h

Отклонение факта от модели за прошлые сутки составило x%, прогноз на следующие 24 часа отклонение sum_model_next2_24h - sum_cold_next2_24h или y%

/****	текст для прогноза на 24, 48 часов	****/

create table diffr_model_cold_5min_3 as (
select
a.*
,case when diffr_prev_24h <= 1.54 then 'Норма за прошлые сутки'
	  when prcnt_diffr_prev_24h >= 0.1 then 'Инцидент за прошлые сутки'
	  else 'Предупреждение за прошлые сутки'
	end as Word_Prev_24
,case when diffr_next_24h <= 1.54 then 'Прогноз на 24ч - норма'
	  when prcnt_diffr_next_24h >= 0.1 then 'Прогноз на 24ч - инцидент'
	  else 'Прогноз на 24ч - предупреждение'
	end as Word_next_24
,case when diffr_next2_24h <= 1.54 then 'Прогноз на 48ч - норма'
	  when prcnt_diffr_next_24h >= 0.1 then 'Прогноз на 48ч - инцидент'
	  else 'Прогноз на 48ч - предупреждение'
	end as Word_next_48
from (
	select
	id_house
	,ds
	,abs(sum_model_prev_24h - sum_cold_prev_24h) as diffr_prev_24h
	,abs(sum_model_prev_24h - sum_cold_prev_24h)/sum_model_prev_24h as prcnt_diffr_prev_24h
	,abs(sum_model_next_24h - sum_cold_next_24h) as diffr_next_24h
	,abs(sum_model_next_24h - sum_cold_next_24h)/sum_model_next_24h as prcnt_diffr_next_24h
	,abs(sum_model_next2_24h - sum_cold_next2_24h) as diffr_next2_24h
	,abs(sum_model_next2_24h - sum_cold_next2_24h)/sum_model_next2_24h as prcnt_diffr_next2_24h
	from diffr_model_cold_5min_2
	) a
);

select * from diffr_model_cold_5min_3
where id_house = 3000



SELECT string_agg(column_name, ', ' ORDER BY ordinal_position)
FROM information_schema.columns 
WHERE table_name = 'diffr_model_cold_5min_2';
id_house, ds, yhat, water_consumption, diffr_cold_mdl, diffr_ratio_5min, sum_model_prev_24h, sum_diffr_prev_24h, sum_abs_diffr_prev_24h, sum_cold_prev_24h, sum_model_next_24h, sum_diffr_next_24h, sum_abs_diffr_next_24h, sum_cold_next_24h, sum_model_next2_24h, sum_diffr_next2_24h, sum_abs_diffr_next2_24h, sum_cold_next2_24h, cnt_difr10_prev24h, cnt_difr10_next24h, cnt_difr10_next2_24h


/****	сбой - линейный тренд *****/
select *
from public.water_lintrend_3000
limit 20

