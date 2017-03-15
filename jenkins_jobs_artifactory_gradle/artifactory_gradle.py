import xml.etree.ElementTree as XML
import jenkins_jobs.modules.base
from jenkins_jobs.errors import JenkinsJobsException

from jenkins_jobs.modules.helpers import artifactory_common_details
from jenkins_jobs.modules.helpers import artifactory_deployment_patterns
from jenkins_jobs.modules.helpers import artifactory_env_vars_patterns
from jenkins_jobs.modules.helpers import artifactory_optional_props

from jenkins_jobs.modules.helpers import convert_mapping_to_xml

import logging

def gradle_properties(xml_parent, data):

    str_props = [
        ('ivy-pattern', 'ivyPattern', '[organisation]/[module]/ivy-[revision].xml'),
        ('artifact-pattern', 'artifactPattern', '[organisation]/[module]/[revision]/[artifact]-[revision](-[classifier]).[ext]'),
        ('default-promotion-target-repository', 'defaultPromotionTargetRepository', ''),
    ]

    for (xml_prop, yaml_prop, default_value) in str_props:
        XML.SubElement(xml_parent, xml_prop).text = data.get(yaml_prop, default_value)

    bool_props = [
        ('not-m2-compatible', 'notM2Compatible', False),
        ('pass-identified-downstream', 'passIdentifiedDownstream', False),
        ('skip-inject-init-script', 'skipInjectInitScript', False),
        ('allow-promotion-of-non-staged-builds', 'allowPromotionOfNonStagedBuilds', False),
        ('allow-bintray-push-of-non-stage-builds', 'allowBintrayPushOfNonStageBuilds', False),
        ('deploy-maven', 'deployMaven', True),
        ('deploy-ivy', 'deployIvy', False),
    ]

    convert_mapping_to_xml(xml_parent, data, bool_props, fail_required=True)

def credentials_config(xml_parent, data, target):
    """ target can be deployer or resolver """

    cred_id = data.get( target + '-credentials-id', '')

    XML.SubElement(xml_parent, 'credentialsId').text = cred_id

    # if cred_id is empty - do not override
    XML.SubElement(xml_parent, 'overridingCredentials').text = str(
        bool(cred_id)
    ).lower()

def artifactory_repository(xml_parent, data, target, prefix='deploy-'):
    if 'release' in target:
        XML.SubElement(xml_parent, 'keyFromText').text = data.get(
            prefix + 'release-repo-key', '')
        XML.SubElement(xml_parent, 'keyFromSelect').text = data.get(
            prefix + 'release-repo-key', '')
        XML.SubElement(xml_parent, 'dynamicMode').text = str(
            data.get(prefix + 'dynamic-mode', False)).lower()

    if 'snapshot' in target:
        XML.SubElement(xml_parent, 'keyFromText').text = data.get(
            prefix + 'snapshot-repo-key', '')
        XML.SubElement(xml_parent, 'keyFromSelect').text = data.get(
            prefix + 'snapshot-repo-key', '')
        XML.SubElement(xml_parent, 'dynamicMode').text = str(
            data.get(prefix + 'dynamic-mode', False)).lower()


def artifactory_gradle(registry, xml_parent, data):
    """yaml: artifactory-gradle
    Wrapper for Artifactory-Gradle integration. Requires the
    :jenkins-wiki:`Artifactory Plugin <Artifactory+Plugin>`

    :arg str url: URL of the Artifactory server. e.g.
        https://www.jfrog.com/artifactory/ (default '')
    :arg str name: Artifactory user with permissions use for
        connected to the selected Artifactory Server
        (default '')
    :arg str key-from-select: Repository key to use (plugin >= 2.3.0)
        (default '')
    :arg str key-from-text: Repository key to use that can be configured
        dynamically using Jenkins variables (plugin >= 2.3.0) (default '')
    :arg list deploy-pattern: List of patterns for mappings
        build artifacts to published artifacts. Supports Ant-style wildcards
        mapping to target directories. E.g.: */*.zip=>dir (default [])
    :arg list resolve-pattern: List of references to other
        artifacts that this build should use as dependencies.
    :arg list matrix-params: List of properties to attach to all deployed
        artifacts in addition to the default ones: build.name, build.number,
        and vcs.revision (default [])
    :arg bool deploy-build-info: Deploy jenkins build metadata with
        artifacts to Artifactory (default false)
    :arg bool env-vars-include: Include environment variables accessible by
        the build process. Jenkins-specific env variables are always included.
        Use the env-vars-include-patterns and env-vars-exclude-patterns to
        filter the environment variables published to artifactory.
        (default false)
    :arg list env-vars-include-patterns: List of environment variable patterns
        for including env vars as part of the published build info. Environment
        variables may contain the * and the ? wildcards (default [])
    :arg list env-vars-exclude-patterns: List of environment variable patterns
        that determine the env vars excluded from the published build info
        (default [])
    :arg bool discard-old-builds:
        Remove older build info from Artifactory (default false)
    :arg bool discard-build-artifacts:
        Remove older build artifacts from Artifactory (default false)

    """
    logger = logging.getLogger("%s:artifactory_gradle" % __name__)


    if data is None:
        data = dict()


    artifactory = XML.SubElement(
        xml_parent,
        'org.jfrog.hudson.gradle.ArtifactoryGradleConfigurator',
    )

    artifactory.set('plugin', 'artifactory@2.6.0')


    # Set details

    details = XML.SubElement(artifactory, 'details')
    artifactory_common_details(details, data)

    XML.SubElement(details, 'repositoryKey').text = data.get(
        'repo-key', '')
    XML.SubElement(details, 'snapshotsRepositoryKey').text = data.get(
        'snapshot-repo-key', '')
    deploy_release = XML.SubElement(details, 'deployReleaseRepository')
    artifactory_repository(deploy_release, data, 'release')

    deploy_snapshot = XML.SubElement(details, 'deploySnapshotRepository')
    artifactory_repository(deploy_snapshot, data, 'snapshot')

    XML.SubElement(details, 'stagingPlugin').text = data.get(
        'resolve-staging-plugin', '')

    # Set cred id's

    deployer_credentials_config = XML.SubElement(details, 'deployerCredentialsConfig')
    credentials_config(deployer_credentials_config, data, 'deployer')

    resolver_credentials_config = XML.SubElement(details, 'resolverCredentialsConfig')
    credentials_config(resolver_credentials_config, data, 'resolver')

    # Set envVarsPatterns
    artifactory_env_vars_patterns(artifactory, data)

    # Set deploymentPatterns
    artifactory_deployment_patterns(artifactory, data)

    # Set resolverDetails

    resolver = XML.SubElement(artifactory, 'resolverDetails')
    artifactory_common_details(resolver, data)

    resolve_snapshot = XML.SubElement(resolver, 'resolveSnapshotRepository')
    artifactory_repository(resolve_snapshot, data, 'snapshot', prefix='resolve-')

    resolve_release = XML.SubElement(resolver, 'resolveReleaseRepository')
    artifactory_repository(resolve_release, data, 'release', prefix='resolve-')

    XML.SubElement(resolver, 'stagingPlugin').text = data.get(
        'resolve-staging-plugin', '')


    XML.SubElement(artifactory, 'discardOldBuilds').text = str(
        data.get('discard-old-builds', False)).lower()
    XML.SubElement(artifactory, 'discardBuildArtifacts').text = str(
        data.get('discard-build-artifacts', True)).lower()
    XML.SubElement(artifactory, 'matrixParams').text = ','.join(
        data.get('matrix-params', []))

    # optional__props
    artifactory_optional_props(artifactory, data, 'wrappers')

    gradle_properties(artifactory, data)
