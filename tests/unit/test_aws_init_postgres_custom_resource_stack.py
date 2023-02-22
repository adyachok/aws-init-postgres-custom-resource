import aws_cdk as core
import aws_cdk.assertions as assertions

from aws_init_postgres_custom_resource.aws_init_postgres_custom_resource_stack import AwsInitPostgresCustomResourceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in aws_init_postgres_custom_resource/aws_init_postgres_custom_resource_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AwsInitPostgresCustomResourceStack(app, "aws-init-postgres-custom-resource")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
