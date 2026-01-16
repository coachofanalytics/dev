import importlib
from types import SimpleNamespace


def test_main_views_handlers(monkeypatch):
    # Monkeypatch django.shortcuts.render to avoid template rendering
    called = {}

    def fake_render(request, template_name, *args, **kwargs):
        called['template'] = template_name
        return SimpleNamespace(status=kwargs.get('status', 200), template=template_name)

    monkeypatch.setattr('django.shortcuts.render', fake_render, raising=False)

    views = importlib.import_module('coda_project.views')
    fake_request = SimpleNamespace()
    res = views.hendler400(fake_request, exception=None)
    assert res.template == '400.html'
    res = views.hendler403(fake_request, exception=None)
    assert res.template == '403.html'
    res = views.hendler404(fake_request, exception=None)
    assert res.template == '404.html'
