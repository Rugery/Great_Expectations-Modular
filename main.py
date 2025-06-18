import json
import pandas as pd
import great_expectations as gx
from datetime import datetime
from great_expectations.checkpoint import UpdateDataDocsAction
from great_expectations.core.run_identifier import RunIdentifier
from checkpoint import create_or_update_checkpoint
from expectation import expectations_iris, expectations_titanic
from suite import create_or_update_suite
from validation import create_validation_definition


def validate_table(table_name, df, expectations, parameters=None):
    context = gx.get_context(mode="file")

    # Crear fuente de datos pandas
    data_source_name = f"pandas_{datetime.now().strftime('%H%M%S')}"
    data_source = context.data_sources.add_pandas(name=data_source_name)
    data_asset = data_source.add_dataframe_asset(name=table_name)
    batch_definition = data_asset.add_batch_definition_whole_dataframe("batch_inicial")

    batch_parameters = {"dataframe": df}
    suite = create_or_update_suite(context, table_name, expectations)
    validation_def = create_validation_definition(context, batch_definition, suite, table_name)
    checkpoint = create_or_update_checkpoint(
        context,
        f"checkpoint_{table_name}",
        [validation_def],
        actions=[UpdateDataDocsAction(name="update_all_data_docs")]
    )

    run_id = RunIdentifier(run_name=f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    result = checkpoint.run(
        batch_parameters=batch_parameters,
        expectation_parameters=parameters or {},
        run_id=run_id
    )

    print(f"\n✅ Resultado del checkpoint '{table_name}':")
    #print(result)

    # Acumular filas que no cumplen en un DataFrame
    all_failed_rows = []
    
    for res in result.run_results.values():
        for r in res["results"]:
            if not r["success"]:
                config = r["expectation_config"]
                kwargs = config.kwargs
                col = kwargs.get("column")
                unexpected_idx = r["result"].get("unexpected_index_list", [])
                if col and unexpected_idx:
                    failed_rows = df.loc[unexpected_idx].copy()
                    failed_rows["failed_column"] = col
                    expectation_type = config.to_json_dict().get("type")
                    failed_rows["expectation"] = expectation_type
                    expected_values = ""
                    if expectation_type == "expect_column_values_to_be_in_set":
                        value_set = kwargs.get("value_set", "")
                        if isinstance(value_set, (list, set)):
                            expected_values = json.dumps(list(value_set))
                        else:
                            expected_values = str(value_set)
                    elif expectation_type in ("expect_column_values_to_be_between", "expect_column_mean_to_be_between"):
                        min_value = kwargs.get("min_value", "")
                        max_value = kwargs.get("max_value", "")
                        expected_values = f"min: {min_value}, max: {max_value}"
                    elif expectation_type == "expect_column_values_to_not_be_null":
                        expected_values = "No null values allowed"
                    else:
                        expected_values = json.dumps(kwargs)  # para otros casos mostrar todos los kwargs
                    
                    failed_rows["expected_values"] = [expected_values] * len(failed_rows)
                    all_failed_rows.append(failed_rows)


    # Concatenar todas las filas que fallan
    if all_failed_rows:
        failed_df = pd.concat(all_failed_rows).drop_duplicates()
    else:
        failed_df = pd.DataFrame()  # vacío si todo pasa

    return failed_df




# -------------------------
# Configuración y ejecución
# -------------------------

if __name__ == "__main__": 
    tables_config = [
        {
            "table_name": "iris_dataset",
            "url": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
            "expectations": expectations_iris,
            "parameters": {"valid_iris_targets": ["versicolor", "virginica"]}
        },
        {
            "table_name": "titanic_dataset",
            "url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
            "expectations": expectations_titanic,
            "parameters": {}
        }
    ]

    failed_dfs = {}

    for config in tables_config:
        df = pd.read_csv(config["url"])
        failed_df = validate_table(
            table_name=config["table_name"],
            df=df,
            expectations=config["expectations"](),
            parameters=config["parameters"]
        )
        failed_dfs[config["table_name"]] = failed_df

    # Guardar cada DataFrame con filas fallidas en CSV, si hay filas fallidas
    for table_name, failed_df in failed_dfs.items():
        if not failed_df.empty:
            failed_df.to_csv(f"{table_name}_quarentine.csv", index=False)
            print(f"Guardadas filas fallidas para {table_name} en {table_name}_quarentine.csv")
        else:
            print(f"No hay filas fallidas para {table_name}")
