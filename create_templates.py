templates_data = [
    ("marketplace/templates/marketplace/update_business_profile.html", """{% extends "base.html" %}

{% block title %}Update Business Profile{% endblock %}

{% block content %}
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card shadow">
                <div class="card-header bg-primary text-white">
                    <h3 class="mb-0"><i class="bi bi-building"></i> Update Business Profile</h3>
                </div>
                <div class="card-body p-4">
                    <form method="post">
                        {% csrf_token %}
                        {% for field in form %}
                            <div class="mb-3">
                                <label class="form-label">{{ field.label }}</label>
                                {{ field }}
                                {% if field.errors %}
                                    <div class="text-danger">{{ field.errors }}</div>
                                {% endif %}
                            </div>
                        {% endfor %}
                        
                        <div class="d-flex justify-content-between mt-4">
                            <a href="{% url 'business_dashboard' %}" class="btn btn-secondary">
                                <i class="bi bi-arrow-left"></i> Cancel
                            </a>
                            <button type="submit" class="btn btn-primary">
                                <i class="bi bi-save"></i> Save Profile
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}"""),
]

for path, content in templates_data:
    with open(path, "w") as f:
        f.write(content)
    print(f"Created: {path}")
