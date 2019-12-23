from django.contrib import admin


class UserAdmin(admin.ModelAdmin):
    list_display = ["pk", "name", "age"]
    list_filter = ["name", "age"]

    # 定制action具体方案
    def func(self, request,queryset):
        queryset.update(age=44)

    func.short_description = "批量初始化操作"
