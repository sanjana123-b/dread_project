from django.contrib import admin
from .models import Project, Threat


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'threat_count', 'average_risk', 'updated_at')
    search_fields = ('name', 'owner__username')


@admin.register(Threat)
class ThreatAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'dread_score', 'risk_level', 'status', 'updated_at')
    list_filter = ('status', 'stride_category', 'project')
    search_fields = ('title', 'description')
