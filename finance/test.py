import os
def financial_services(request):
    import requests
    base_currency = request.GET.get('base', 'USD')
    amount = float(request.GET.get('amount', 1))
    EXCHANGE_API_KEY = os.getenv('EXCHANGE_API_KEY')
    print("key is : ", EXCHANGE_API_KEY)
    url = f"https://v6.exchangerate-api.com/v6/24c20b412a3ba72f197d6e66/latest/USD"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        print("response : ",response)
        print("data: ",data)
        if data.get("result") == "success" and "KES" in data["conversion_rates"]:
            kes_rate = data["conversion_rates"]["KES"]
            converted = amount * kes_rate
        else:
            kes_rate = None
            converted = None
            print("⚠️ Unexpected API response:", data)

    except Exception as e:
        kes_rate = None
        converted = None
        print("🚨 API fetch error:", e)

    context = {
        'base_currency': base_currency,
        'kes_rate': kes_rate,
        'converted': converted,
        'amount': amount,
        'date': data.get('time_last_update_utc', 'N/A'),
    }

    return render(request, "finance/financial_services.html", context)
