from subprocess import CalledProcessError
from typing import TYPE_CHECKING

from pydantic import BaseModel

from applications.inproj.models.dependency import Dependency, DependencyType
from applications.inproj.models.lock_file import LockFile, LockFileType
from applications.inproj.models.project import Project
from applications.inproj.models.project_artefact import ProjectArtefact
from applications.inproj.models.version_object import VersionObject
from applications.inproj.models.vulnerability import Vulnerability
from core.database.mongodb import MongoDBHandler
from core.tasks.task import Task
from core.tasks.types import TaskData

if TYPE_CHECKING:
    from core.context.context import Context


class ProcessLockfileTask(Task["ProcessLockfileTask.InputModel"]):

    class InputModel(BaseModel):
        project: Project
        artefact: ProjectArtefact
        lock_file: LockFile

    async def _process(self, context: "Context", data_in: TaskData) -> TaskData:

        input_data_object = self.input_object(data_in)
        project = input_data_object.project
        artefact = input_data_object.artefact
        lock_file = input_data_object.lock_file

        if lock_file.type == LockFileType.POETRY:
            import json
            import subprocess

            dependency_location = f"{project.name}:{artefact.name}"
            # here call pip-audit

            try:
                result = subprocess.check_output(["pip-audit", "-f", "json"])
            except CalledProcessError as e:
                result = e.output

            result_as_dict = json.loads(result)

            result_dependencies = result_as_dict["dependencies"]

            dependencies = []
            all_vulnerabilities = []
            all_vunerabilities_ids = []
            for dependency in result_dependencies:
                dependencies.append(
                    Dependency(
                        location=dependency_location,
                        name=dependency["name"],
                        version=VersionObject.from_pypy_text(dependency["version"]),
                        type=DependencyType.PYTHON,
                        vulnerabilities=[vuln["id"] for vuln in dependency["vulns"]],
                    )
                )

                for vuln in dependency["vulns"]:
                    all_vulnerabilities.append(
                        Vulnerability(
                            vuln_id=vuln["id"],
                            aliases=vuln["aliases"],
                            dependency=dependency["name"],
                            type=DependencyType.PYTHON,
                            fix_versions=[
                                VersionObject.from_pypy_text(fix_version)
                                for fix_version in vuln["fix_versions"]
                            ],
                            description=vuln["description"],
                            artefacts_concerned=[dependency_location],
                        )
                    )
                    all_vunerabilities_ids.append(vuln["id"])

            lock_file.dependencies = dependencies

            mongodb_handler = MongoDBHandler.from_default(context)
            mongodb_handler.update_object(context, project)

            current_artefact_vulnerabilities = mongodb_handler.load_multiples(
                Vulnerability.META_MODEL, {"artefacts_concerned": dependency_location}
            )

            current_vuln_id_set = set()
            for current_vuln in current_artefact_vulnerabilities:
                current_vuln.add(current_vuln.vuln_id)

            existing_vulnerabilities = mongodb_handler.load_multiples(
                Vulnerability.META_MODEL, {"vuln_id": {"$in": all_vunerabilities_ids}}
            )

            found_vuln_id_set = set()
            for existing_vuln in existing_vulnerabilities:
                if dependency_location not in existing_vuln.artefacts_concerned:
                    existing_vuln.artefacts_concerned.append(dependency_location)
                    mongodb_handler.update_object(
                        context, existing_vuln, Vulnerability.META_MODEL
                    )

                found_vuln_id_set.add(existing_vuln.vuln_id)

            for vuln in all_vulnerabilities:
                if vuln.vuln_id in current_vuln_id_set:
                    current_vuln_id_set.remove(vuln.vuln_id)
                if vuln.vuln_id in found_vuln_id_set:
                    # already existing
                    continue

                mongodb_handler.save_object(context, vuln, Vulnerability.META_MODEL)

            for current_vuln in current_artefact_vulnerabilities:
                if current_vuln.vuln_id not in current_vuln_id_set:
                    continue

                mongodb_handler.delete_model_object(
                    context, current_vuln, Vulnerability.META_MODEL
                )

        return {}
