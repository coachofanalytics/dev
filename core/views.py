"""
Core app views - Landing page and public-facing pages
"""
from django.shortcuts import render
from django.http import Http404


def landing_page(request):
    context = {
        "page_title": "Biashara Bridges - Building International Business Connections",
        "meta_description": "Connecting businesses, investors, and governments between Kenya, the U.S., and the world.",
    }
    return render(request, "core/landing.html", context)


def about_page(request):
    context = {
        "page_title": "About Us - Biashara Bridges",
        "meta_description": "Learn about Biashara Bridges LLC, a U.S. and Kenya-registered company.",
    }
    return render(request, "core/about.html", context)


def services_page(request):
    context = {
        "page_title": "Our Services - Biashara Bridges",
        "meta_description": "Diaspora Investment Facilitation, Trade Partnerships, Events.",
    }
    return render(request, "core/services.html", context)


def projects_page(request):
    context = {
        "page_title": "Our Projects - Biashara Bridges",
        "meta_description": "Machakos County, AggreBind, Diaspora Engagement.",
    }
    return render(request, "core/projects.html", context)


def project_detail(request, slug):
    projects = {
        "machakos-county": {
            "title": "Machakos County Partnership",
            "template": "core/project_machakos.html",
        },
        "aggrebind": {
            "title": "AggreBind Solutions Partnership",
            "template": "core/project_aggrebind.html",
        },
        "diaspora-engagement": {
            "title": "Diaspora Engagement",
            "template": "core/project_diaspora.html",
        },
    }
    if slug not in projects:
        raise Http404("Project not found")
    project = projects[slug]
    context = {"page_title": project["title"], "project_slug": slug}
    return render(request, project["template"], context)


def partners_page(request):
    context = {"page_title": "Our Partners - Biashara Bridges"}
    return render(request, "core/partners.html", context)


def gallery_page(request):
    context = {"page_title": "Gallery - Biashara Bridges"}
    return render(request, "core/gallery.html", context)


def news_page(request):
    all_articles = [
        {"slug": "diaspora-policy-2025", "title": "Diaspora Policy 2025 Launch", "date": "Sep 5, 2025", "category": "Meetings", "excerpt": "Historic policy launch.", "image": "news/article1.jpg"},
        {"slug": "sdda-meeting", "title": "SDDA Meeting", "date": "Sep 5, 2025", "category": "Meetings", "excerpt": "Courtesy visit to SDDA.", "image": "news/article2.jpg"},
        {"slug": "kenya-ohio-visit", "title": "Kenya-Ohio Visit", "date": "Sep 5, 2025", "category": "Events", "excerpt": "Trade discussions.", "image": "news/article3.jpg"},
        {"slug": "governor-meeting", "title": "Governor Wavinya Meeting", "date": "Sep 5, 2025", "category": "Meetings", "excerpt": "Machakos investments.", "image": "news/article4.jpg"},
    ]

    # Get unique categories with counts
    categories = {}
    for article in all_articles:
        cat = article["category"]
        categories[cat] = categories.get(cat, 0) + 1

    # Filter by category if specified
    selected_category = request.GET.get("category", "")
    if selected_category:
        articles = [a for a in all_articles if a["category"] == selected_category]
    else:
        articles = all_articles

    context = {
        "page_title": "News - Biashara Bridges",
        "articles": articles,
        "all_articles": all_articles,
        "categories": categories,
        "selected_category": selected_category,
    }
    return render(request, "core/news.html", context)


def news_detail(request, slug):
    articles = {
        "diaspora-policy-2025": {"title": "Diaspora Policy 2025 Launch", "date": "Sep 5, 2025", "content": "<p>Historic policy launch content.</p>"},
        "sdda-meeting": {"title": "SDDA Meeting", "date": "Sep 5, 2025", "content": "<p>SDDA meeting content.</p>"},
        "kenya-ohio-visit": {"title": "Kenya-Ohio Visit", "date": "Sep 5, 2025", "content": "<p>Kenya-Ohio visit content.</p>"},
        "governor-meeting": {"title": "Governor Meeting", "date": "Sep 5, 2025", "content": "<p>Governor meeting content.</p>"},
    }
    if slug not in articles:
        raise Http404("Article not found")
    article = articles[slug]
    context = {"page_title": article["title"], "article": article}
    return render(request, "core/news_detail.html", context)


def contact_page(request):
    context = {"page_title": "Contact Us - Biashara Bridges"}
    return render(request, "core/contact.html", context)
