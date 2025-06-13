import boto3


class EBEnvironmentStatus:
    Launching = 'Launching'
    Updating = 'Updating'
    Ready = 'Ready'
    Terminating = 'Terminating'
    Terminated = 'Terminated'
    Unknown = 'Unknown'


class ElasticBeanstalkManager:
    def __init__(self):
        self.role = 'ElasticBeanstalkManager'
        self.client = boto3.client('elasticbeanstalk')

    def create_environment(self, environment_name: str,
                           application_name: str,
                           stack_name: str,
                           template_name: str,
                           description: str,
                           tags: list,
                           environment_variables: dict, proceed_when_exists: bool = False):
        try:
            option_settings = [
                {
                    'Namespace': 'aws:elasticbeanstalk:application:environment',
                    'OptionName': key,
                    'Value': value
                } for key, value in environment_variables.items()
            ]

            if environment_name is None:
                raise ValueError(f"[{self.role}] Environment name is required")
            if application_name is None:
                raise ValueError(f"[{self.role}] Application name is required")

            version_label = None
            try:
                version_label = self.get_latest_application_version_label(application_name)
                print(f"[{self.role}] Latest version label: {version_label}")
            except Exception as e:
                print(f"[{self.role}] error: {e}")

            args = {
                "EnvironmentName": environment_name,
                "ApplicationName": application_name,
                "Tags": tags,
                "OptionSettings": option_settings,
                "Tier": {
                      "Name": "WebServer",
                      "Type": "Standard",
                      "Version": "1.0"
                },
                "Description": description,
            }

            if version_label is not None:
                print(f"[{self.role}] Using version label: {version_label}")
                args['VersionLabel'] = version_label

            if stack_name is None:
                if template_name is None:
                    args['TemplateName'] = "template-" + application_name
                else:
                    print(f"[{self.role}] Using stack name: {stack_name}")
                    args['TemplateName'] = template_name
            else:
                print(f"[{self.role}] Using template name: {template_name}")
                args['SolutionStackName'] = stack_name
            print(f"[{self.role}] initiating environment create")
            return self.client.create_environment(**args)
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def terminate_environment(self, environment_name: str):
        try:
            # validate environment exists
            environment = self.get_environment_status(environment_name)
            if not environment:
                print(f"[{self.role}] Environment {environment_name} not found")
                return
            if environment.get('status', None) in [EBEnvironmentStatus.Terminating, EBEnvironmentStatus.Terminated]:
                print(f"[{self.role}] Environment {environment_name} is already terminating or terminated")
                return
            print(f"[{self.role}] Terminating environment {environment_name}")
            response = self.client.terminate_environment(
                EnvironmentName=environment_name,
                TerminateResources=True
            )
            print(f"[{self.role}] Environment {environment_name} terminated")
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise

    def get_environment_id_by_application_name(self, application_name: str):
        try:
            response = self.client.describe_environments(
                ApplicationName=application_name,
                MaxRecords=3,
                IncludeDeleted=True
            )
            environments = response.get('Environments', [])
            if not environments:
                print(f"[{self.role}] Environment not found for application {application_name}")
                return
            environment = environments[0]
            return environment.get('EnvironmentId')
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise

    def create_configuration_template(self, application_name: str, environment_name: str):
        try:
            print(f"[{self.role}] Getting example environment id for application {application_name}")
            env_id = (
                self.get_environment_id_by_environment_name(application_name=application_name,
                                                            environment_name=environment_name))
            args = {
                "ApplicationName": application_name,
                "TemplateName": "template-" + application_name,
                "EnvironmentId": env_id
            }
            print(f"[{self.role}] Creating configuration template for application {application_name}, args: {args}")
            result = self.client.create_configuration_template(**args)
            print(f"[{self.role}] Configuration template created for application {application_name}")
            return result
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def get_latest_application_version_label(self, application_name: str):
        try:
            response = self.client.describe_application_versions(
                ApplicationName=application_name,
                MaxRecords=1
            )
            versions = response.get('ApplicationVersions', [])
            if not versions:
                print(f"[{self.role}] Application version not found for application {application_name}")
                return
            # sort versions by date
            versions.sort(key=lambda x: x.get('DateCreated'), reverse=True)
            version = versions[0]
            return version.get('VersionLabel')
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise

    def update_environment_with_latest_version(self, environment_name: str, application_name: str):
        try:
            version_label = self.get_latest_application_version_label(application_name)
            if version_label is None:
                print(f"[{self.role}] Application version not found for application {application_name}")
                return
            print(f"[{self.role}] Updating environment {environment_name} with version {version_label}")
            response = self.client.update_environment(
                EnvironmentName=environment_name,
                VersionLabel=version_label
            )
            return response
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

    def restart_environment(self, environment_name: str):
        try:
            response = self.client.restart_app_server(
                EnvironmentName=environment_name
            )
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def rebuild_environment(self, environment_name: str):
        try:
            response = self.client.rebuild_environment(
                EnvironmentName=environment_name
            )
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def validate_e2e_environment(self, environment_name: str, domain_name: str):
        try:
            # restart the environment
            response = self.restart_environment(environment_name)
            print(f"[{self.role}] Restarted environment {environment_name}")

            # wait until environment to be green
            import time
            max_retries = 15
            count = 0
            while True:
                count += 1
                response = self.get_environment_status(environment_name)
                if response.get('status') == EBEnvironmentStatus.Ready:
                    print(f"[{self.role}] Environment is ready")
                    break
                if count >= max_retries:
                    print(f"[{self.role}] environment not ready after 5 minutes, finish")
                    raise Exception(f"[{self.role}] environment not ready after 5 minutes")
                time.sleep(30)

            # check the domain e2e if it is 200
            import requests
            url = f"https://{domain_name}"
            response = requests.get(url)
            print(f"[{self.role}] Domain {domain_name} status code: {response.status_code}")
            if response.status_code != 200:
                raise Exception(f"[{self.role}] Domain {domain_name} not reachable")
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def retrieve_environment_logs(self, environment_name: str):
        try:
            print(f"[{self.role}] Retrieving environment logs for {environment_name}")
            response = self.client.request_environment_info(
                EnvironmentName=environment_name,
                InfoType='tail'
            )
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def describe_environment_health(self, environment_name: str):
        try:
            response = self.client.describe_events(
                EnvironmentName=environment_name,
                MaxRecords=200,
                Severity='WARN'
            )
            return response
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise e

    def get_environment_id_by_environment_name(self, application_name: str, environment_name: str) -> str | None:
        try:
            response = self.client.describe_environments(
                EnvironmentNames=[environment_name],
                ApplicationName=application_name,
            )
            environments = response.get('Environments', [])
            if not environments:
                print(f"[{self.role}] Environment not found for environment {environment_name}")
                return
            environment = environments[0]
            return environment.get('EnvironmentId')
        except Exception as e:
            print(f"[{self.role}] error: {e}")
            raise

    def delete_configuration_template(self, application_name: str, template_name: str) -> dict:
        try:
            response = self.client.delete_configuration_template(
                ApplicationName=application_name,
                TemplateName=template_name
            )
            print(
                f"Configuration template '{template_name}' for application '{application_name}' deleted successfully.")
            return response
        except Exception as e:
            print(f"Failed to delete configuration template: {e}")
