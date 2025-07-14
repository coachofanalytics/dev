# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Projects(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    engagement_code = models.CharField(max_length=255)
    engagement_type = models.CharField(max_length=255)
    partner = models.CharField(max_length=100)
    is_active = models.BooleanField()
    creator_name = models.CharField(max_length=255)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'projects'
        verbose_name_plural = 'projects'


class Access(models.Model):
    user_id = models.UUIDField(primary_key=True)
    project = models.ForeignKey(Projects, on_delete=models.CASCADE)
    access_level = models.CharField(max_length=200)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'access'
        unique_together = (('user_id', 'project', 'id'),)
        verbose_name_plural = 'access'


class Status(models.Model):
    name = models.CharField(max_length=255)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'status'
        verbose_name_plural = 'status'


class Roles(models.Model):
    name = models.CharField(max_length=255)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'
        verbose_name_plural = 'roles'


class NormalizedTitles(models.Model):
    name = models.CharField(max_length=255)
    onet_code = models.CharField(max_length=255)
    version = models.IntegerField()
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'normalized_titles'
        verbose_name_plural = 'normalized_titles'


class Titles(models.Model):
    name = models.CharField(max_length=255)
    normalized_title = models.ForeignKey(NormalizedTitles, models.CASCADE, blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'titles'
        verbose_name_plural = 'titles'


class Locations(models.Model):
    name = models.CharField(max_length=255)
    esri_response = models.CharField(max_length=255, blank=True, null=True)
    latitude = models.CharField(max_length=50, blank=True, null=True)
    longitude = models.CharField(max_length=50, blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'locations'
        verbose_name_plural = 'locations'


class Industry(models.Model):
    level1 = models.CharField(max_length=200)
    level2 = models.CharField(max_length=200, blank=True, null=True)
    level3 = models.CharField(max_length=200, blank=True, null=True)
    level4 = models.CharField(max_length=200, blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'industry'
        verbose_name_plural = 'industry'


class Departments(models.Model):
    bus_unit = models.CharField(max_length=100, blank=True, null=True)
    bus_func = models.CharField(max_length=100, blank=True, null=True)
    bus_subfunc = models.CharField(max_length=100, blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'departments'
        verbose_name_plural = 'departments'


class Persons(models.Model):
    employee_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.ForeignKey(Titles, models.DO_NOTHING, blank=True, null=True)
    location = models.ForeignKey(Locations, models.DO_NOTHING, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=100, blank=True, null=True)
    base_compensation = models.FloatField(blank=True, null=True)
    bonus = models.FloatField(blank=True, null=True)
    fringe_benefits = models.FloatField(blank=True, null=True)
    fully_loaded_compensation = models.FloatField()
    hire_date = models.DateField(blank=True, null=True)
    exit_date = models.DateField(blank=True, null=True)
    employee_type = models.CharField(max_length=100, blank=True, null=True)
    years_of_service = models.IntegerField(blank=True, null=True)
    race_ethnicity = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField()
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'persons'
        verbose_name_plural = 'persons'


class PersonRole(models.Model):
    person = models.OneToOneField(Persons, models.CASCADE, primary_key=True)
    role = models.ForeignKey(Roles, models.DO_NOTHING)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'person_role'
        unique_together = (('person', 'role', 'id'),)
        verbose_name_plural = 'person_role'


class Orgs(models.Model):
    project = models.ForeignKey(Projects, models.CASCADE)
    industry = models.ForeignKey(Industry, models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True, null=True)
    is_sub_org = models.BooleanField()
    sub_org_desc = models.CharField(max_length=200, blank=True, null=True)
    preceding_org_id = models.UUIDField(blank=True, null=True)
    is_benchmarkable = models.BooleanField()
    is_benchmark = models.BooleanField()
    is_internal = models.BooleanField()
    is_global_external = models.BooleanField()
    published = models.BooleanField()
    published_searchable = models.BooleanField(blank=True, null=True)
    published_date = models.DateField(blank=True, null=True)
    publication_venue = models.CharField(max_length=200, blank=True, null=True)
    published_state = models.CharField(max_length=200, blank=True, null=True)
    total_conversations = models.FloatField(blank=True, null=True)
    low_span_threshold = models.IntegerField(blank=True, null=True)
    is_low_span_threshold_changed = models.BooleanField(blank=True, null=True)
    is_accessed = models.BooleanField()
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orgs'
        verbose_name_plural = 'orgs'


class Positions(models.Model):
    title = models.ForeignKey(Titles, models.CASCADE, blank=True, null=True)
    location = models.ForeignKey(Locations, models.CASCADE, blank=True, null=True)
    dept = models.ForeignKey(Departments, models.CASCADE, blank=True, null=True)
    copy_position_id = models.UUIDField(blank=True, null=True)
    role_type = models.CharField(max_length=200, blank=True, null=True)
    base_compensation = models.FloatField(blank=True, null=True)
    bonus = models.FloatField(blank=True, null=True)
    fringe_benefits = models.FloatField(blank=True, null=True)
    fully_loaded_compensation = models.FloatField()
    is_active = models.BooleanField()
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'positions'
        verbose_name_plural = 'positions'


class PositionRole(models.Model):
    position = models.OneToOneField(Positions, models.CASCADE, primary_key=True)
    role = models.ForeignKey(Roles, models.CASCADE)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'position_role'
        unique_together = (('position', 'role', 'id'),)
        verbose_name_plural = 'position_role'


class OrgHier(models.Model):
    org = models.ForeignKey(Orgs, models.CASCADE)
    parent_position = models.ForeignKey(Positions, models.CASCADE, blank=True, null=True, related_name='parent_position')
    position = models.ForeignKey(Positions, models.CASCADE, related_name='position')
    layer = models.IntegerField(blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'org_hier'
        verbose_name_plural = 'org_hier'


class ExtPositions(models.Model):
    position = models.ForeignKey(Positions, models.CASCADE)
    raw_data = models.TextField()  # This field type is a guess.
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ext_positions'
        verbose_name_plural = 'ext_positions'


class ExtPersons(models.Model):
    person = models.ForeignKey(Persons, models.CASCADE)
    raw_data = models.TextField()  # This field type is a guess.
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'ext_persons'
        verbose_name_plural = 'ext_persons'


class BenchmarkFact(models.Model):
    org_id = models.UUIDField()
    industry_id = models.UUIDField()
    dept_id = models.UUIDField(blank=True, null=True)
    normalized_title_id = models.UUIDField(blank=True, null=True)
    location_id = models.UUIDField(blank=True, null=True)
    total_employees = models.BigIntegerField()
    total_individual_contributors = models.BigIntegerField()
    total_managers = models.BigIntegerField()
    total_base_compensation = models.FloatField(blank=True, null=True)
    total_bonus = models.FloatField(blank=True, null=True)
    total_fringe_benefits = models.FloatField(blank=True, null=True)
    total_fully_loaded_compensation = models.FloatField(blank=True, null=True)
    avg_base_compensation = models.FloatField(blank=True, null=True)
    avg_bonus = models.FloatField(blank=True, null=True)
    avg_fringe_benefits = models.FloatField(blank=True, null=True)
    avg_fully_loaded_compensation = models.FloatField(blank=True, null=True)
    total_ic_base_compensation = models.FloatField(blank=True, null=True)
    total_ic_bonus = models.FloatField(blank=True, null=True)
    total_ic_fringe_benefits = models.FloatField(blank=True, null=True)
    total_ic_fully_loaded_compensation = models.FloatField(blank=True, null=True)
    id = models.UUIDField(primary_key=True)
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'benchmark_fact'
        verbose_name_plural = 'benchmark_fact'


class AssociationOrgPosition(models.Model):
    org = models.OneToOneField(Orgs, models.CASCADE, primary_key=True)
    position = models.ForeignKey(Positions, models.CASCADE)
    low_span_threshold = models.IntegerField(blank=True, null=True)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True,null=True)

    class Meta:
        managed = False
        db_table = 'association_org_position'
        unique_together = (('org', 'position', 'id'),)
        verbose_name_plural = 'association_org_position'


class AssociationOrgPersonPosition(models.Model):
    org = models.OneToOneField(Orgs, models.CASCADE, primary_key=True)
    position = models.ForeignKey(Positions, models.CASCADE)
    person = models.ForeignKey(Persons, models.CASCADE)
    status = models.ForeignKey(Status, models.CASCADE)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'association_org_person_position'
        unique_together = (('org', 'position', 'person', 'id'),)
        verbose_name_plural = 'association_org_person_position'


class AssociationOrgPerson(models.Model):
    org = models.OneToOneField(Orgs, models.CASCADE, primary_key=True)
    person = models.ForeignKey(Persons, models.CASCADE)
    id = models.UUIDField()
    created_by = models.UUIDField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_by = models.UUIDField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'association_org_person'
        unique_together = (('org', 'person', 'id'),)
        verbose_name_plural = 'association_org_person'
