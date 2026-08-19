from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from analysis.models import Project, Threat
from analysis.templatetags.threatscope import (
    risk_color, risk_tint, risk_glyph, status_color, status_bg,
    stride_abbr, factor_color, pct_of_ten, dread_spine_micro,
    dread_spine_card, dread_spine_hero, risk_bar
)


class ThreatScopeModelsAndTagsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.project = Project.objects.create(name='Test Project', description='Testing desc', owner=self.user)
        self.threat1 = Threat.objects.create(
            project=self.project,
            title='Critical SQLi',
            description='SQL Injection',
            stride_category='tampering',
            damage=9,
            reproducibility=9,
            exploitability=9,
            affected_users=9,
            discoverability=9,
            status='open',
            created_by=self.user
        )
        self.threat2 = Threat.objects.create(
            project=self.project,
            title='Low Info Leak',
            description='Header disclosure',
            stride_category='info_disclosure',
            damage=2,
            reproducibility=3,
            exploitability=2,
            affected_users=2,
            discoverability=1,
            status='mitigated',
            created_by=self.user
        )

    def test_model_properties(self):
        # Threat 1
        self.assertEqual(self.threat1.dread_score, 9.0)
        self.assertEqual(self.threat1.risk_level, 'Critical')
        self.assertEqual(self.threat1.risk_color, '#dc2626')

        # Threat 2
        self.assertEqual(self.threat2.dread_score, 2.0)
        self.assertEqual(self.threat2.risk_level, 'Low')

        # Project properties
        self.assertEqual(self.project.threat_count, 2)
        self.assertEqual(self.project.average_risk, 5.5)
        self.assertEqual(self.project.max_score, 9.0)
        self.assertEqual(self.project.max_risk_level, 'Critical')
        
        breakdown = self.project.risk_breakdown
        self.assertEqual(breakdown['Critical'], 1)
        self.assertEqual(breakdown['Low'], 1)
        self.assertEqual(breakdown['High'], 0)
        self.assertEqual(breakdown['Medium'], 0)

    def test_templatetags(self):
        self.assertEqual(risk_color('Critical'), '#FF3D71')
        self.assertEqual(risk_tint('High'), 'rgba(255,138,61,0.12)')
        self.assertEqual(risk_glyph('Critical'), '◆')
        self.assertEqual(status_color('Open'), '#8B9CB8')
        self.assertEqual(status_bg('Mitigated'), 'rgba(34,211,165,0.1)')
        self.assertEqual(stride_abbr('Tampering'), 'T')
        self.assertEqual(factor_color(10), '#FF3D71')
        self.assertEqual(pct_of_ten(8), 80.0)

        # Inclusions
        micro = dread_spine_micro(self.threat1)
        self.assertEqual(len(micro['segments']), 5)
        
        card = dread_spine_card(self.threat1)
        self.assertEqual(len(card['segments']), 5)

        hero = dread_spine_hero(self.threat1)
        self.assertEqual(hero['score'], 9.0)

        bar = risk_bar(self.project.risk_breakdown)
        self.assertEqual(bar['total'], 2)

        # Defensive fallback when passed a string or None
        bar_fallback = risk_bar("")
        self.assertEqual(bar_fallback['total'], 0)


class ThreatScopeViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='alice', email='alice@example.com', password='password123')
        self.other_user = User.objects.create_user(username='bob', password='password123')
        self.project = Project.objects.create(name='Alice Project', description='Desc', owner=self.user)
        self.threat = Threat.objects.create(
            project=self.project,
            title='Sample Threat',
            description='Sample desc',
            stride_category='spoofing',
            damage=5,
            reproducibility=5,
            exploitability=5,
            affected_users=5,
            discoverability=5,
            status='open',
            created_by=self.user
        )

    def test_auth_required_redirects(self):
        urls = [
            reverse('dashboard'),
            reverse('project_list'),
            reverse('project_create'),
            reverse('project_detail', kwargs={'pk': self.project.pk}),
            reverse('project_edit', kwargs={'pk': self.project.pk}),
            reverse('project_delete', kwargs={'pk': self.project.pk}),
            reverse('threat_create', kwargs={'project_pk': self.project.pk}),
            reverse('threat_detail', kwargs={'pk': self.threat.pk}),
            reverse('threat_edit', kwargs={'pk': self.threat.pk}),
            reverse('threat_delete', kwargs={'pk': self.threat.pk}),
            reverse('export_csv', kwargs={'project_pk': self.project.pk}),
        ]
        for url in urls:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 302)

    def test_dashboard_and_lists_authenticated(self):
        self.client.login(username='alice', password='password123')

        # Dashboard
        res = self.client.get(reverse('dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Alice Project')
        self.assertContains(res, 'Sample Threat')

        # Project list
        res = self.client.get(reverse('project_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Alice Project')

    def test_project_crud(self):
        self.client.login(username='alice', password='password123')

        # Create
        res = self.client.post(reverse('project_create'), {
            'name': 'New Web App',
            'description': 'Description for new app'
        })
        self.assertEqual(res.status_code, 302)
        new_project = Project.objects.get(name='New Web App')
        self.assertEqual(new_project.owner, self.user)

        # Detail
        res = self.client.get(reverse('project_detail', kwargs={'pk': new_project.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'New Web App')

        # Edit
        res = self.client.post(reverse('project_edit', kwargs={'pk': new_project.pk}), {
            'name': 'Updated Web App',
            'description': 'Updated description'
        })
        self.assertEqual(res.status_code, 302)
        new_project.refresh_from_db()
        self.assertEqual(new_project.name, 'Updated Web App')

        # Delete GET (confirmation page)
        res = self.client.get(reverse('project_delete', kwargs={'pk': new_project.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Updated Web App')

        # Delete POST
        res = self.client.post(reverse('project_delete', kwargs={'pk': new_project.pk}))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Project.objects.filter(pk=new_project.pk).exists())

    def test_threat_crud(self):
        self.client.login(username='alice', password='password123')

        # Create Threat
        res = self.client.post(reverse('threat_create', kwargs={'project_pk': self.project.pk}), {
            'title': 'XSS Vulnerability',
            'description': 'Reflected XSS on search bar',
            'stride_category': 'tampering',
            'damage': 7,
            'reproducibility': 8,
            'exploitability': 6,
            'affected_users': 8,
            'discoverability': 6,
            'status': 'open',
            'mitigation': 'Sanitize inputs and use CSP'
        })
        self.assertEqual(res.status_code, 302)
        threat = Threat.objects.get(title='XSS Vulnerability')
        self.assertEqual(threat.project, self.project)
        self.assertEqual(threat.dread_score, 7.0)
        self.assertEqual(threat.risk_level, 'High')

        # Detail
        res = self.client.get(reverse('threat_detail', kwargs={'pk': threat.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'XSS Vulnerability')
        self.assertContains(res, 'High')

        # Edit
        res = self.client.post(reverse('threat_edit', kwargs={'pk': threat.pk}), {
            'title': 'XSS Vulnerability (Resolved)',
            'description': 'Reflected XSS on search bar',
            'stride_category': 'tampering',
            'damage': 7,
            'reproducibility': 8,
            'exploitability': 6,
            'affected_users': 8,
            'discoverability': 6,
            'status': 'mitigated',
            'mitigation': 'CSP and escaping applied'
        })
        self.assertEqual(res.status_code, 302)
        threat.refresh_from_db()
        self.assertEqual(threat.title, 'XSS Vulnerability (Resolved)')
        self.assertEqual(threat.status, 'mitigated')

        # Delete
        res = self.client.post(reverse('threat_delete', kwargs={'pk': threat.pk}))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Threat.objects.filter(pk=threat.pk).exists())

    def test_export_csv(self):
        self.client.login(username='alice', password='password123')
        res = self.client.get(reverse('export_csv', kwargs={'project_pk': self.project.pk}))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'text/csv')
        self.assertIn('Sample Threat', res.content.decode('utf-8'))

    def test_user_isolation(self):
        # Bob cannot access Alice's project or threat
        self.client.login(username='bob', password='password123')

        res = self.client.get(reverse('project_detail', kwargs={'pk': self.project.pk}))
        self.assertEqual(res.status_code, 404)

        res = self.client.get(reverse('threat_detail', kwargs={'pk': self.threat.pk}))
        self.assertEqual(res.status_code, 404)

        res = self.client.post(reverse('threat_delete', kwargs={'pk': self.threat.pk}))
        self.assertEqual(res.status_code, 404)
