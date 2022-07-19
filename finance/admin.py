from django.contrib import admin

# Register your models here.
from django.urls import path, reverse
from .models import  Payment_History,Default_Payment_Fees,Transaction,Inflow,Outflow,Payment_Information #, DocUpload
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("sender", "receiver", "amount")

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [
            path("upload-csv/", self.upload_csv),
        ]
        return new_urls + urls

    def upload_csv(self, request):

        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]

            if not csv_file.name.endswith(".csv"):
                messages.warning(
                    request, "The wrong file type was uploaded, it should be a csv file"
                )
                return HttpResponseRedirect(request.path_info)

            # file= csv_file.read().decode("utf-8")
            file = csv_file.read().decode("ISO-8859-1")
            file_data = file.split("\n")
            csv_data = [line for line in file_data if line.strip() != ""]
            print(csv_data)
            for x in csv_data:
                fields = x.split(",")
                created = Transaction.objects.update_or_create(
                    activity_date=fields[0],
                    sender=fields[1],
                    receiver=fields[2],
                    phone=fields[3],
                    qty=fields[4],
                    amount=fields[5],
                    payment_method=fields[6],
                    department=fields[7],
                    category=fields[8],
                    type=fields[9],
                    description=fields[10],
                    receipt_link=fields[11],
                )
            url = reverse("admin:index")
            return HttpResponseRedirect(url)
        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(Inflow)
admin.site.register(Outflow)
admin.site.register(Payment_History)
admin.site.register(Payment_Information)
admin.site.register(Default_Payment_Fees)