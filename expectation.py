import great_expectations as gx

def expectations_iris():
    return [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="sepal_length"),
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="sepal_length", min_value=1.0, max_value=2.0
        ),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="species", value_set={"$PARAMETER": "valid_iris_targets"}
        )
    ]


def expectations_titanic():
    query_Sex_Male = """ SELECT * FROM {batch} WHERE Sex != 'male'"""
    Sex_Description = "El genero del pasajero debe ser hombre"
    # expect_Sex_Male = gx.expectations.UnexpectedRowsExpectation(
    # unexpected_rows_query=query_Sex_Male,
    # description=Sex_Description,
    # meta={"name": "expect_only_males_in_Sex_column"}
    # )
    expect_Sex_Male = gx.expectations.ExpectColumnValuesToBeInSet(
    column="Sex",
    value_set=["Male"],
    meta={
        "name": "Regla de calidad hombre",
        "description": "El genero del pasajero debe ser hombre"}
    )
    return [
       # gx.expectations.ExpectColumnValuesToNotBeNull(column="Age"),
        #gx.expectations.ExpectColumnValuesToBeBetween(
         #   column="Age", min_value=0, max_value=100
        #),
        #gx.expectations.ExpectColumnValuesToBeInSet(
         #   column="Survived", value_set=[0, 1]
        #),
        #gx.expectations.ExpectColumnValuesToBeInSet(
         #   column="Embarked", value_set=["S","C"]
       # ),   
        expect_Sex_Male,   
    ]
