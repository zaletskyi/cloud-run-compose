import fire
import random
from populate import populate_string
import os.path
from .support import load, temporary_write, subprocess_call
import yaml

here = os.path.dirname(__file__)

CREDENTIALS = """

provider "google-beta" {
  credentials = file("${{ credentialsJson }}")
  project     = "${{projectId}}"
  region      = "us-central1"
}

provider "google" {
  credentials = file("${{ credentialsJson }}")
  project     = var.projectId
  region      = "us-central1"
}
"""


SERVICE_PLAN = r"""
resource "google_cloud_run_service" "${{ serviceName }}" {
  provider = google-beta
  name     = "${{ serviceName }}"
  location = "${{ region }}"
  metadata {
    namespace = "${{ projectId }}"
  }

  template {
    spec {
      containers {
        image = "${{ image }}"
        command = "${{ command }}"
        args = "${{ args }}"
        env = [
            ${{
                indent_to('            ', '\n'.join(['{\n    name = "' + name + '"\n    value = "' + value + '"\n},' for name, value in environment.items()]))
            }}
        ]
      }
    }
  }
}

output "${{serviceName}}service_url" {
  value = "${google_cloud_run_service.${{serviceName}}.status[0].url}"
}
"""


# plan = load(os.path.join(here, "main.tf"))


def get_environment(config):
    env = config.get("environment")
    if isinstance(env, dict):
        return env
    if isinstance(env, list):
        result = {}
        for line in env:
            k, _, v = line.partition("=")
            result[k] = v
        return result
    return {}


def main(projectId="pp1", file="docker-compose.yml", region="us-central1"):
    config = yaml.safe_load(open(file))
    for serviceName, service in config.get("services", {}).items():
        vars = dict(
            environment=get_environment(service),
            serviceName=serviceName,
            image=service.get("image", ""),
            command=service.get("entrypoint", ""),
            args=service.get("command", ""),
            region=region,
            projectId=projectId,
        )
        populated_service = populate_string(SERVICE_PLAN, vars)
        print(populated_service)
    # random_dir = str(random.random())[3:]
    # with temporary_write(
    #     populated_plan, delete_dir=True, path=os.path.join(here, random_dir, "main.tf")
    # ) as plan_path:
    #     out = subprocess_call("cat " + plan_path)
    #     print(out)


fire.Fire(main)
