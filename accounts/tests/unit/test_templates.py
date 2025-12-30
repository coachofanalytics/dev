@login_required
def test_payment_template_render(request):
    return render(
        request,
        'accounts/payment_history_list.html',
        {'payments': []}
    )
