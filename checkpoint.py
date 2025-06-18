import great_expectations as gx
from great_expectations.exceptions import DataContextError

def create_or_update_checkpoint(context, checkpoint_name, validation_definitions, actions):
    try:
        checkpoint = context.checkpoints.get(checkpoint_name)
        checkpoint.validation_definitions = validation_definitions
        checkpoint.actions = actions
        checkpoint.save()
    except DataContextError:
        checkpoint = gx.Checkpoint(
            name=checkpoint_name,
            validation_definitions=validation_definitions,
            actions=actions,
            result_format={"result_format": "COMPLETE"},
        )
        context.checkpoints.add(checkpoint)
    return checkpoint
