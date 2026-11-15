{{ config_cadastro('TERRITORIO', 'municipio_consolidado', ['codigo'], 'Município consolidado: todos os atributos territoriais e o porte populacional. A INT_MOV valida o código de município aqui.') }}
select t.*,
       case when t.populacao is null then 'NÃO INFORMADO'
            when t.populacao < 20000 then 'PEQUENO I' when t.populacao < 50000 then 'PEQUENO II'
            when t.populacao < 100000 then 'MÉDIO' when t.populacao < 900000 then 'GRANDE' else 'METRÓPOLE' end as porte_populacional
from {{ ref('int_cad_territorio_municipio_populacao') }} t
