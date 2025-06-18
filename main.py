import pandas as pd
import great_expectations as gx
from datetime import datetime
from great_expectations.checkpoint import UpdateDataDocsAction
from great_expectations.core.run_identifier import RunIdentifier
from checkpoint import create_or_update_checkpoint
from expectativas import expectations_iris, expectations_titanic
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
    print(result)


# -------------------------
# Configuración y ejecución
# -------------------------

if __name__ == "__main__": 
    tables_config = [
        {
            "table_name": "iris_dataset",
            "url": "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/iris.csv",
            "expectations": expectations_iris,
            "parameters": {"valid_iris_targets": ["setosa", "versicolor", "virginica"]}
        },
        {
            "table_name": "titanic_dataset",
            "url": "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
            "expectations": expectations_titanic,
            "parameters": {}
        }
    ]

    for config in tables_config:
        df = pd.read_csv(config["url"])
        validate_table(
            table_name=config["table_name"],
            df=df,
            expectations=config["expectations"](),
            parameters=config["parameters"]
        )
