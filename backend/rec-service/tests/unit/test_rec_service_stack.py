import aws_cdk as core
import aws_cdk.assertions as assertions

from rec_service.rec_service_stack import RecServiceStack

# example tests. To run these tests, uncomment this file along with the example
# resource in rec_service/rec_service_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = RecServiceStack(app, "rec-service")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
