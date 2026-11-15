-- Converte texto em data sem derrubar a carga: o DATASUS traz datas inválidas e sentinelas ('00000000', '0000').
-- Formatos usados: 'YYYYMMDD' (SIH), 'DDMMYYYY' (SIM/SINASC), 'YYYYMM' (competência CNES, vira o dia 1).
CREATE OR REPLACE FUNCTION ctl.f_data(texto text, formato text) RETURNS date
LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
    IF texto IS NULL OR texto ~ '^0+$' THEN RETURN NULL; END IF;
    IF formato = 'YYYYMM' THEN RETURN to_date(texto || '01', 'YYYYMMDD'); END IF;
    RETURN to_date(texto, formato);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END $$;

-- Log de execução das cargas (preenchido pelo script de extração).
CREATE TABLE IF NOT EXISTS ctl.ctl_processo_carga (
    id_execucao   bigserial PRIMARY KEY,
    dt_referencia date        NOT NULL,   -- data de referência da carga (= DT_CARGA)
    etapa         text        NOT NULL,   -- 'extracao' ou 'dbt'
    objeto        text        NOT NULL,   -- nome da tabela/modelo
    linhas        bigint,
    segundos      numeric(12,3),
    inicio        timestamp   NOT NULL DEFAULT now()
);
