from __future__ import absolute_import

from rest_framework.response import Response

from sentry.plugins import plugins
from sentry.api.bases.organization import OrganizationEndpoint
from sentry.api.serializers import serialize
from sentry.api.serializers.models.organization_plugin import OrganizationPluginSerializer
from sentry.models import ProjectOption


class OrganizationPluginsEndpoint(OrganizationEndpoint):
    def get(self, request, organization):
        # Just load all Plugins once.
        all_plugins = dict([
            (p.slug, p) for p in plugins.all()
        ])

        if 'plugins' in request.GET:
            desired_plugins = set(request.GET.getlist('plugins'))
        else:
            desired_plugins = set(all_plugins.keys())

        if not desired_plugins.issubset(set(all_plugins.keys())):
            return Response({'detail': 'Invalid plugins'}, status=422)

        # Each tuple represents an enabled Plugin (of only the ones we care
        # about) and its corresponding Project.
        enabled_plugins = ProjectOption.objects.filter(
            key__in=['%s:enabled' % slug for slug in desired_plugins],
            project__organization=organization,
        ).select_related('project')

        resources = []

        for project_option in enabled_plugins:
            resources.append(
                serialize(
                    all_plugins[project_option.key.split(':')[0]],
                    request.user,
                    OrganizationPluginSerializer(project_option.project),
                )
            )

        return Response(resources)
