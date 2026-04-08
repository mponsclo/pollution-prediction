{% macro generate_schema_name(custom_schema_name, node) -%}
    {#
        Use the custom schema name directly as the BigQuery dataset name.
        Without this macro, dbt would generate "default_schema_custom_schema"
        (e.g. "dbt_landing" instead of just "landing").
    #}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
