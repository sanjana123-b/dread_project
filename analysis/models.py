from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class Project(models.Model):
    """A system/application being threat-modeled."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project_detail', args=[self.pk])

    @property
    def threat_count(self):
        return self.threats.count()

    @property
    def average_risk(self):
        threats = self.threats.all()
        if not threats:
            return 0
        return round(sum(t.dread_score for t in threats) / len(threats), 2)

    @property
    def risk_breakdown(self):
        """Count of threats per severity category, for charting."""
        breakdown = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
        for t in self.threats.all():
            breakdown[t.risk_level] += 1
        return breakdown

    @property
    def max_score(self):
        threats = self.threats.all()
        if not threats:
            return 0
        return max(t.dread_score for t in threats)

    @property
    def max_risk_level(self):
        threats = self.threats.all()
        if not threats:
            return None
        max_threat = max(threats, key=lambda t: t.dread_score)
        return max_threat.risk_level


class Threat(models.Model):
    """
    A single threat scored using the DREAD model:
    Damage, Reproducibility, Exploitability, Affected Users, Discoverability.
    Each rated 1 (low) - 10 (high). Risk score = average of the five.
    """

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Risk Accepted'),
        ('false_positive', 'False Positive'),
    ]

    RATING_CHOICES = [(i, str(i)) for i in range(1, 11)]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='threats')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    stride_category = models.CharField(
        max_length=30,
        choices=[
            ('spoofing', 'Spoofing'),
            ('tampering', 'Tampering'),
            ('repudiation', 'Repudiation'),
            ('info_disclosure', 'Information Disclosure'),
            ('denial_of_service', 'Denial of Service'),
            ('elevation_of_privilege', 'Elevation of Privilege'),
            ('other', 'Other'),
        ],
        default='other',
        blank=True,
    )

    # DREAD ratings
    damage = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
        help_text="How severe is the damage if this threat is exploited?")
    reproducibility = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
        help_text="How easily can the attack be reproduced?")
    exploitability = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
        help_text="How much effort/skill is needed to exploit it?")
    affected_users = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
        help_text="How many users/systems would be affected?")
    discoverability = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5,
        help_text="How easy is it for an attacker to discover this threat?")

    mitigation = models.TextField(blank=True, help_text="Recommended mitigation / remediation plan")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.project.name})"

    def get_absolute_url(self):
        return reverse('threat_detail', args=[self.pk])

    @property
    def dread_score(self):
        """Average of the five DREAD ratings, rounded to 2 decimals."""
        total = (
            self.damage + self.reproducibility + self.exploitability
            + self.affected_users + self.discoverability
        )
        return round(total / 5, 2)

    @property
    def risk_level(self):
        score = self.dread_score
        if score >= 8:
            return 'Critical'
        elif score >= 6:
            return 'High'
        elif score >= 4:
            return 'Medium'
        return 'Low'

    @property
    def risk_color(self):
        return {
            'Critical': '#dc2626',
            'High': '#f97316',
            'Medium': '#eab308',
            'Low': '#22c55e',
        }[self.risk_level]
