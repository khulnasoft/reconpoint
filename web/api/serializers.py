from dashboard.models import *
from django.contrib.humanize.templatetags.humanize import (naturalday, naturaltime)
from django.db.models import F, JSONField, Value
from recon_note.models import *
from reconPoint.common_func import *
from rest_framework import serializers
from scanEngine.models import *
from startScan.models import *
from targetApp.models import *
from dashboard.models import InAppNotification


class HackerOneProgramAttributesSerializer(serializers.Serializer):
	"""
		Serializer for HackerOne Program
		IMP: THIS is not a model serializer, programs will not be stored in db
		due to ever changing nature of programs, rather cache will be used on these serializers
	"""
	handle = serializers.CharField(required=False)
	name = serializers.CharField(required=False)
	currency = serializers.CharField(required=False)
	submission_state = serializers.CharField(required=False)
	triage_active = serializers.BooleanField(allow_null=True, required=False)
	state = serializers.CharField(required=False)
	started_accepting_at = serializers.DateTimeField(required=False)
	bookmarked = serializers.BooleanField(required=False)
	allows_bounty_splitting = serializers.BooleanField(required=False)
	offers_bounties = serializers.BooleanField(required=False)
	open_scope = serializers.BooleanField(allow_null=True, required=False)
	fast_payments = serializers.BooleanField(allow_null=True, required=False)
	gold_standard_safe_harbor = serializers.BooleanField(allow_null=True, required=False)

	@staticmethod
	def to_representation(instance):
		return {key: value for key, value in instance.items()}


class HackerOneProgramSerializer(serializers.Serializer):
	id = serializers.CharField()
	type = serializers.CharField()
	attributes = HackerOneProgramAttributesSerializer()



class InAppNotificationSerializer(serializers.ModelSerializer):
	class Meta:
		model = InAppNotification
		fields = [
			'id', 
			'title', 
			'description', 
			'icon', 
			'is_read', 
			'created_at', 
			'notification_type', 
			'status',
			'redirect_link',
			'open_in_new_tab',
			'project'
		]
		read_only_fields = ['id', 'created_at']

	@staticmethod
	def get_project_name(obj):
		return obj.project.name if obj.project else None


class SearchHistorySerializer(serializers.ModelSerializer):
	class Meta:
		model = SearchHistory
		fields = ['query']


class DomainSerializer(serializers.ModelSerializer):
	vuln_count = serializers.SerializerMethodField()
	organization = serializers.SerializerMethodField()
	most_recent_scan = serializers.SerializerMethodField()
	insert_date = serializers.SerializerMethodField()
	insert_date_humanized = serializers.SerializerMethodField()
	start_scan_date = serializers.SerializerMethodField()
	start_scan_date_humanized = serializers.SerializerMethodField()

	class Meta:
		model = Domain
		fields = '__all__'
		depth = 2

	@staticmethod
	def get_vuln_count(obj):
		try:
			return obj.vuln_count
		except:
			return None

	@staticmethod
	def get_organization(obj):
		if Organization.objects.filter(domains__id=obj.id).exists():
			return [org.name for org in Organization.objects.filter(domains__id=obj.id)]

	@staticmethod
	def get_most_recent_scan(obj):
		return obj.get_recent_scan_id()

	@staticmethod
	def get_insert_date(obj):
		return naturalday(obj.insert_date).title()

	@staticmethod
	def get_insert_date_humanized(obj):
		return naturaltime(obj.insert_date).title()

	@staticmethod
	def get_start_scan_date(obj):
		if obj.start_scan_date:
			return naturalday(obj.start_scan_date).title()

	@staticmethod
	def get_start_scan_date_humanized(obj):
		if obj.start_scan_date:
			return naturaltime(obj.start_scan_date).title()


class SubScanResultSerializer(serializers.ModelSerializer):

	task = serializers.SerializerMethodField('get_task_name')
	subdomain_name = serializers.SerializerMethodField('get_subdomain_name')
	engine = serializers.SerializerMethodField('get_engine_name')

	class Meta:
		model = SubScan
		fields = [
			'id',
			'type',
			'subdomain_name',
			'start_scan_date',
			'stop_scan_date',
			'scan_history',
			'subdomain',
			'celery_ids',
			'status',
			'subdomain_name',
			'task',
			'engine'
		]

	@staticmethod
	def get_subdomain_name(subscan):
		return subscan.subdomain.name

	@staticmethod
	def get_task_name(subscan):
		return subscan.type

	@staticmethod
	def get_engine_name(subscan):
		if subscan.engine:
			return subscan.engine.engine_name
		return ''


class ReconNoteSerializer(serializers.ModelSerializer):

	domain_name = serializers.SerializerMethodField('get_domain_name')
	subdomain_name = serializers.SerializerMethodField('get_subdomain_name')
	scan_started_time = serializers.SerializerMethodField('get_scan_started_time')

	class Meta:
		model = TodoNote
		fields = '__all__'

	@staticmethod
	def get_domain_name(note):
		if note.scan_history:
			return note.scan_history.domain.name

	@staticmethod
	def get_subdomain_name(note):
		if note.subdomain:
			return note.subdomain.name

	@staticmethod
	def get_scan_started_time(note):
		if note.scan_history:
			return note.scan_history.start_scan_date


class OnlySubdomainNameSerializer(serializers.ModelSerializer):
	class Meta:
		model = Subdomain
		fields = ['name', 'id']


class SubScanSerializer(serializers.ModelSerializer):

	subdomain_name = serializers.SerializerMethodField('get_subdomain_name')
	time_taken = serializers.SerializerMethodField('get_total_time_taken')
	elapsed_time = serializers.SerializerMethodField('get_elapsed_time')
	completed_ago = serializers.SerializerMethodField('get_completed_ago')
	engine = serializers.SerializerMethodField('get_engine_name')

	class Meta:
		model = SubScan
		fields = '__all__'

	@staticmethod
	def get_subdomain_name(subscan):
		return subscan.subdomain.name

	@staticmethod
	def get_total_time_taken(subscan):
		return subscan.get_total_time_taken()

	@staticmethod
	def get_elapsed_time(subscan):
		return subscan.get_elapsed_time()

	@staticmethod
	def get_completed_ago(subscan):
		return subscan.get_completed_ago()

	@staticmethod
	def get_engine_name(subscan):
		if subscan.engine:
			return subscan.engine.engine_name
		return ''


class CommandSerializer(serializers.ModelSerializer):
	class Meta:
		model = Command
		fields = '__all__'
		depth = 1


class ScanHistorySerializer(serializers.ModelSerializer):

	subdomain_count = serializers.SerializerMethodField('get_subdomain_count')
	endpoint_count = serializers.SerializerMethodField('get_endpoint_count')
	vulnerability_count = serializers.SerializerMethodField('get_vulnerability_count')
	current_progress = serializers.SerializerMethodField('get_progress')
	completed_time = serializers.SerializerMethodField('get_total_scan_time_in_sec')
	elapsed_time = serializers.SerializerMethodField('get_elapsed_time')
	completed_ago = serializers.SerializerMethodField('get_completed_ago')
	organizations = serializers.SerializerMethodField('get_organizations')

	class Meta:
		model = ScanHistory
		fields = [
			'id',
			'subdomain_count',
			'endpoint_count',
			'vulnerability_count',
			'current_progress',
			'completed_time',
			'elapsed_time',
			'completed_ago',
			'organizations',
			'start_scan_date',
			'scan_status',
			'results_dir',
			'celery_ids',
			'tasks',
			'stop_scan_date',
			'error_message',
			'domain',
			'scan_type'
		]
		depth = 1

	@staticmethod
	def get_subdomain_count(scan_history):
		if scan_history.get_subdomain_count:
			return scan_history.get_subdomain_count()

	@staticmethod
	def get_endpoint_count(scan_history):
		if scan_history.get_endpoint_count:
			return scan_history.get_endpoint_count()

	@staticmethod
	def get_vulnerability_count(scan_history):
		if scan_history.get_vulnerability_count:
			return scan_history.get_vulnerability_count()

	@staticmethod
	def get_progress(scan_history):
		return scan_history.get_progress()

	@staticmethod
	def get_total_scan_time_in_sec(scan_history):
		return scan_history.get_total_scan_time_in_sec()

	@staticmethod
	def get_elapsed_time(scan_history):
		return scan_history.get_elapsed_time()

	@staticmethod
	def get_completed_ago(scan_history):
		return scan_history.get_completed_ago()

	@staticmethod
	def get_organizations(scan_history):
		return [org.name for org in scan_history.domain.get_organization()]


class OrganizationSerializer(serializers.ModelSerializer):

	class Meta:
		model = Organization
		fields = '__all__'


class EngineSerializer(serializers.ModelSerializer):

	tasks = serializers.SerializerMethodField('get_tasks')

	@staticmethod
	def get_tasks(instance):
		return instance.tasks

	class Meta:
		model = EngineType
		fields = [
			'id',
			'default_engine',
			'engine_name',
			'yaml_configuration',
			'tasks'
		]


class OrganizationTargetsSerializer(serializers.ModelSerializer):

	class Meta:
		model = Domain
		fields = [
			'name'
		]


class VisualiseVulnerabilitySerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')

	class Meta:
		model = Vulnerability
		fields = [
			'description',
			'http_url'
		]

	@staticmethod
	def get_description(vulnerability):
		return vulnerability.name


class VisualisePortSerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')
	title = serializers.SerializerMethodField('get_title')

	class Meta:
		model = Port
		fields = [
			'description',
			'is_uncommon',
			'title',
		]

	@staticmethod
	def get_description(port):
		return str(port.number) + "/" + str(port.service_name)

	@staticmethod
	def get_title(port):
		if port.is_uncommon:
			return "Uncommon Port"


class VisualiseTechnologySerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')

	class Meta:
		model = Technology
		fields = [
			'description'
		]

	@staticmethod
	def get_description(tech):
		return tech.name


class VisualiseIpSerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')
	children = serializers.SerializerMethodField('get_children')

	class Meta:
		model = IpAddress
		fields = [
			'description',
			'children'
		]

	@staticmethod
	def get_description(Ip):
		return Ip.address

	@staticmethod
	def get_children(ip):
		port = Port.objects.filter(
			ports__in=IpAddress.objects.filter(
				address=ip))
		serializer = VisualisePortSerializer(port, many=True)
		return serializer.data


class VisualiseEndpointSerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')

	class Meta:
		model = EndPoint
		fields = [
			'description',
			'http_url'
		]

	@staticmethod
	def get_description(endpoint):
		return endpoint.http_url


class VisualiseSubdomainSerializer(serializers.ModelSerializer):

	children = serializers.SerializerMethodField('get_children')
	description = serializers.SerializerMethodField('get_description')
	title = serializers.SerializerMethodField('get_title')

	class Meta:
		model = Subdomain
		fields = [
			'description',
			'children',
			'http_status',
			'title',
		]

	@staticmethod
	def get_description(subdomain):
		return subdomain.name

	@staticmethod
	def get_title(subdomain):
		if get_interesting_subdomains(subdomain.scan_history.id).filter(name=subdomain.name).exists():
			return "Interesting"

	def get_children(self, subdomain_name):
		scan_history = self.context.get('scan_history')
		subdomains = (
			Subdomain.objects
			.filter(scan_history=scan_history)
			.filter(name=subdomain_name)
		)

		ips = IpAddress.objects.filter(ip_addresses__in=subdomains)
		ip_serializer = VisualiseIpSerializer(ips, many=True)

		# endpoint = EndPoint.objects.filter(
		#     scan_history=self.context.get('scan_history')).filter(
		#     subdomain__name=subdomain_name)
		# endpoint_serializer = VisualiseEndpointSerializer(endpoint, many=True)

		technologies = Technology.objects.filter(technologies__in=subdomains)
		tech_serializer = VisualiseTechnologySerializer(technologies, many=True)

		vulnerability = (
			Vulnerability.objects
			.filter(scan_history=scan_history)
			.filter(subdomain=subdomain_name)
		)

		return_data = []
		if ip_serializer.data:
			return_data.append({
				'description': 'IPs',
				'children': ip_serializer.data
			})
		# if endpoint_serializer.data:
		#     return_data.append({
		#         'description': 'Endpoints',
		#         'children': endpoint_serializer.data
		#     })
		if tech_serializer.data:
			return_data.append({
				'description': 'Technologies',
				'children': tech_serializer.data
			})

		if vulnerability:
			vulnerability_data = []
			critical = vulnerability.filter(severity=4)
			if critical:
				critical_serializer = VisualiseVulnerabilitySerializer(
					critical,
					many=True
				)
				vulnerability_data.append({
					'description': 'Critical',
					'children': critical_serializer.data
				})
			high = vulnerability.filter(severity=3)
			if high:
				high_serializer = VisualiseVulnerabilitySerializer(
					high,
					many=True
				)
				vulnerability_data.append({
					'description': 'High',
					'children': high_serializer.data
				})
			medium = vulnerability.filter(severity=2)
			if medium:
				medium_serializer = VisualiseVulnerabilitySerializer(
					medium,
					many=True
				)
				vulnerability_data.append({
					'description': 'Medium',
					'children': medium_serializer.data
				})
			low = vulnerability.filter(severity=1)
			if low:
				low_serializer = VisualiseVulnerabilitySerializer(
					low,
					many=True
				)
				vulnerability_data.append({
					'description': 'Low',
					'children': low_serializer.data
				})
			info = vulnerability.filter(severity=0)
			if info:
				info_serializer = VisualiseVulnerabilitySerializer(
					info,
					many=True
				)
				vulnerability_data.append({
					'description': 'Informational',
					'children': info_serializer.data
				})
			uknown = vulnerability.filter(severity=-1)
			if uknown:
				uknown_serializer = VisualiseVulnerabilitySerializer(
					uknown,
					many=True
				)
				vulnerability_data.append({
					'description': 'Unknown',
					'children': uknown_serializer.data
				})

			if vulnerability_data:
				return_data.append({
					'description': 'Vulnerabilities',
					'children': vulnerability_data
				})

		if subdomain_name.screenshot_path:
			return_data.append({
				'description': 'Screenshot',
				'screenshot_path': subdomain_name.screenshot_path
			})
		return return_data


class VisualiseEmailSerializer(serializers.ModelSerializer):
	title = serializers.SerializerMethodField('get_title')
	description = serializers.SerializerMethodField('get_description')

	class Meta:
		model = Email
		fields = [
			'description',
			'password',
			'title'
		]

	@staticmethod
	def get_description(email):
		if email.password:
			return email.address + " > " + email.password
		return email.address

	@staticmethod
	def get_title(email):
		if email.password:
			return "Exposed Creds"


class VisualiseDorkSerializer(serializers.ModelSerializer):

	title = serializers.SerializerMethodField('get_title')
	description = serializers.SerializerMethodField('get_description')
	http_url = serializers.SerializerMethodField('get_http_url')

	class Meta:
		model = Dork
		fields = [
			'title',
			'description',
			'http_url'
		]

	@staticmethod
	def get_title(dork):
		return dork.type

	@staticmethod
	def get_description(dork):
		return dork.type

	@staticmethod
	def get_http_url(dork):
		return dork.url


class VisualiseEmployeeSerializer(serializers.ModelSerializer):

	description = serializers.SerializerMethodField('get_description')

	class Meta:
		model = Employee
		fields = [
			'description'
		]

	@staticmethod
	def get_description(employee):
		if employee.designation:
			return employee.name + '--' + employee.designation
		return employee.name


class VisualiseDataSerializer(serializers.ModelSerializer):

	title = serializers.ReadOnlyField(default='Target')
	description = serializers.SerializerMethodField('get_description')
	children = serializers.SerializerMethodField('get_children')

	class Meta:
		model = ScanHistory
		fields = [
			'description',
			'title',
			'children',
		]

	@staticmethod
	def get_description(scan_history):
		return scan_history.domain.name

	@staticmethod
	def get_children(history):
		scan_history = ScanHistory.objects.filter(id=history.id)

		subdomain = Subdomain.objects.filter(scan_history=history)
		subdomain_serializer = VisualiseSubdomainSerializer(
			subdomain,
			many=True,
			context={'scan_history': history})

		email = Email.objects.filter(emails__in=scan_history)
		email_serializer = VisualiseEmailSerializer(email, many=True)

		dork = Dork.objects.filter(dorks__in=scan_history)
		dork_serializer = VisualiseDorkSerializer(dork, many=True)

		employee = Employee.objects.filter(employees__in=scan_history)
		employee_serializer = VisualiseEmployeeSerializer(employee, many=True)

		metainfo = MetaFinderDocument.objects.filter(
			scan_history__id=history.id)

		return_data = []

		if subdomain_serializer.data:
			return_data.append({
				'description': 'Subdomains',
				'children': subdomain_serializer.data})

		if email_serializer.data or employee_serializer.data or dork_serializer.data or metainfo:
			osint_data = []
			if email_serializer.data:
				osint_data.append({
					'description': 'Emails',
					'children': email_serializer.data})
			if employee_serializer.data:
				osint_data.append({
					'description': 'Employees',
					'children': employee_serializer.data})
			if dork_serializer.data:
				osint_data.append({
					'description': 'Dorks',
					'children': dork_serializer.data})

			if metainfo:
				metainfo_data = []
				usernames = (
					metainfo
					.annotate(description=F('author'))
					.values('description')
					.distinct()
					.annotate(children=Value([], output_field=JSONField()))
					.filter(author__isnull=False)
				)

				if usernames:
					metainfo_data.append({
						'description': 'Usernames',
						'children': usernames})

				software = (
					metainfo
					.annotate(description=F('producer'))
					.values('description')
					.distinct()
					.annotate(children=Value([], output_field=JSONField()))
					.filter(producer__isnull=False)
				)

				if software:
					metainfo_data.append({
						'description': 'Software',
						'children': software})

				os = (
					metainfo
					.annotate(description=F('os'))
					.values('description')
					.distinct()
					.annotate(children=Value([], output_field=JSONField()))
					.filter(os__isnull=False)
				)

				if os:
					metainfo_data.append({
						'description': 'OS',
						'children': os})

			if metainfo:
				osint_data.append({
					'description':'Metainfo',
					'children': metainfo_data})

			return_data.append({
				'description':'OSINT',
				'children': osint_data})

		return return_data


class SubdomainChangesSerializer(serializers.ModelSerializer):

	change = serializers.SerializerMethodField('get_change')
	is_interesting = serializers.SerializerMethodField('get_is_interesting')

	class Meta:
		model = Subdomain
		fields = '__all__'

	@staticmethod
	def get_change(Subdomain):
		return Subdomain.change

	@staticmethod
	def get_is_interesting(Subdomain):
		return (
			get_interesting_subdomains(Subdomain.scan_history.id)
			.filter(name=Subdomain.name)
			.exists()
		)


class EndPointChangesSerializer(serializers.ModelSerializer):

	change = serializers.SerializerMethodField('get_change')

	class Meta:
		model = EndPoint
		fields = '__all__'

	@staticmethod
	def get_change(EndPoint):
		return EndPoint.change


class InterestingSubdomainSerializer(serializers.ModelSerializer):

	class Meta:
		model = Subdomain
		fields = ['name']


class EmailSerializer(serializers.ModelSerializer):

	class Meta:
		model = Email
		fields = '__all__'


class DorkSerializer(serializers.ModelSerializer):

	class Meta:
		model = Dork
		fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Employee
		fields = '__all__'


class MetafinderDocumentSerializer(serializers.ModelSerializer):

	class Meta:
		model = MetaFinderDocument
		fields = '__all__'
		depth = 1


class MetafinderUserSerializer(serializers.ModelSerializer):

	class Meta:
		model = MetaFinderDocument
		fields = ['author']


class InterestingEndPointSerializer(serializers.ModelSerializer):

	class Meta:
		model = EndPoint
		fields = ['http_url']


class TechnologyCountSerializer(serializers.Serializer):
	count = serializers.CharField()
	name = serializers.CharField()


class DorkCountSerializer(serializers.Serializer):
	count = serializers.CharField()
	type = serializers.CharField()


class TechnologySerializer(serializers.ModelSerializer):
	class Meta:
		model = Technology
		fields = '__all__'


class PortSerializer(serializers.ModelSerializer):
	class Meta:
		model = Port
		fields = '__all__'


class IpSerializer(serializers.ModelSerializer):

	ports = PortSerializer(many=True)

	class Meta:
		model = IpAddress
		fields = '__all__'


class DirectoryFileSerializer(serializers.ModelSerializer):

	class Meta:
		model = DirectoryFile
		fields = '__all__'


class DirectoryScanSerializer(serializers.ModelSerializer):
	scanned_date = serializers.SerializerMethodField()
	formatted_date_for_id = serializers.SerializerMethodField()
	directory_files = DirectoryFileSerializer(many=True)

	class Meta:
		model = DirectoryScan
		fields = '__all__'

	@staticmethod
	def get_scanned_date(DirectoryScan):
		return DirectoryScan.scanned_date.strftime("%b %d, %Y %H:%M")

	@staticmethod
	def get_formatted_date_for_id(DirectoryScan):
		return DirectoryScan.scanned_date.strftime("%b_%d_%Y_%H_%M")


class IpSubdomainSerializer(serializers.ModelSerializer):

	class Meta:
		model = Subdomain
		fields = ['name', 'ip_addresses']
		depth = 1

class WafSerializer(serializers.ModelSerializer):

	class Meta:
		model = Waf
		fields = '__all__'


class SubdomainSerializer(serializers.ModelSerializer):

	vuln_count = serializers.SerializerMethodField('get_vuln_count')

	is_interesting = serializers.SerializerMethodField('get_is_interesting')

	endpoint_count = serializers.SerializerMethodField('get_endpoint_count')
	info_count = serializers.SerializerMethodField('get_info_count')
	low_count = serializers.SerializerMethodField('get_low_count')
	medium_count = serializers.SerializerMethodField('get_medium_count')
	high_count = serializers.SerializerMethodField('get_high_count')
	critical_count = serializers.SerializerMethodField('get_critical_count')
	todos_count = serializers.SerializerMethodField('get_todos_count')
	directories_count = serializers.SerializerMethodField('get_directories_count')
	subscan_count = serializers.SerializerMethodField('get_subscan_count')
	ip_addresses = IpSerializer(many=True)
	waf = WafSerializer(many=True)
	technologies = TechnologySerializer(many=True)
	directories = DirectoryScanSerializer(many=True)


	class Meta:
		model = Subdomain
		fields = '__all__'

	@staticmethod
	def get_is_interesting(subdomain):
		scan_id = subdomain.scan_history.id if subdomain.scan_history else None
		return (
			get_interesting_subdomains(scan_id)
			.filter(name=subdomain.name)
			.exists()
		)

	@staticmethod
	def get_endpoint_count(subdomain):
		return subdomain.get_endpoint_count

	@staticmethod
	def get_info_count(subdomain):
		return subdomain.get_info_count

	@staticmethod
	def get_low_count(subdomain):
		return subdomain.get_low_count

	@staticmethod
	def get_medium_count(subdomain):
		return subdomain.get_medium_count

	@staticmethod
	def get_high_count(subdomain):
		return subdomain.get_high_count

	@staticmethod
	def get_critical_count(subdomain):
		return subdomain.get_critical_count

	@staticmethod
	def get_directories_count(subdomain):
		return subdomain.get_directories_count

	@staticmethod
	def get_subscan_count(subdomain):
		return subdomain.get_subscan_count

	@staticmethod
	def get_todos_count(subdomain):
		return len(subdomain.get_todos.filter(is_done=False))

	@staticmethod
	def get_vuln_count(obj):
		try:
			return obj.vuln_count
		except:
			return None


class EndpointSerializer(serializers.ModelSerializer):

	techs = TechnologySerializer(many=True)

	class Meta:
		model = EndPoint
		fields = '__all__'


class EndpointOnlyURLsSerializer(serializers.ModelSerializer):

	class Meta:
		model = EndPoint
		fields = ['http_url']


class VulnerabilitySerializer(serializers.ModelSerializer):

	discovered_date = serializers.SerializerMethodField()
	severity = serializers.SerializerMethodField()

	@staticmethod
	def get_discovered_date(Vulnerability):
		return Vulnerability.discovered_date.strftime("%b %d, %Y %H:%M")

	@staticmethod
	def get_severity(Vulnerability):
		if Vulnerability.severity == 0:
			return "Info"
		elif Vulnerability.severity == 1:
			return "Low"
		elif Vulnerability.severity == 2:
			return "Medium"
		elif Vulnerability.severity == 3:
			return "High"
		elif Vulnerability.severity == 4:
			return "Critical"
		elif Vulnerability.severity == -1:
			return "Unknown"
		else:
			return "Unknown"

	class Meta:
		model = Vulnerability
		fields = '__all__'
		depth = 2
