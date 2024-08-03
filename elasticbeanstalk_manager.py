import boto3


class ElasticBeanstalkManager:
    def __init__(self):
        self.role = 'ElasticBeanstalkManager'
        self.client = boto3.client('elasticbeanstalk')

    def create_environment(self, environment_name: str,
                           application_name: str,
                           environment_tier: str,
                           description: str,
                           tags: list,
                           environment_variables: dict):
        try:
            option_settings = [
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': key,
                    'Value': value
                } for key, value in environment_variables.items()
            ]

            args = {
                "EnvironmentName": environment_name,
                "ApplicationName": application_name,
                "Tags": tags,
                "OptionSettings": option_settings,
                "environment_tier": environment_tier,
                "environment_variables": environment_variables,
                "Description": description,
            }
            return self.client.create_environment(args)
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def get_environment_status(self, environment_name: str) -> None | dict:
        try:
            response = self.client.describe_environments(
                EnvironmentNames=[environment_name]
            )
            environments = response.get('Environments', [])
            if not environments:
                print(f"[{self.role}] Environment {environment_name} not found.")
                return
            environment = environments[0]
            status = environment.get('Status')
            print(f"[{self.role}] Environment {environment_name} status: {status}")
            return {"status": status, "url": environment.get('CNAME')}
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def list_environments(self):
        return self.client.describe_environments()

