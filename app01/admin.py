from django.contrib import admin
from app01.models import *


class BookConfig(admin.ModelAdmin):
    list_display = ["nid", "title", "price", "publishDate"]  # 定制显示那些列，不能放多对多
    list_display_links = ["title"]  # 查看链接
    # list_filter = ["title", "publishDate", "authors"]  # 过滤
    list_editable = ["price"]  # 编辑
    search_fields = ["title", "price"]  # 搜索字段
    # date_hierarchy = "publishDate"
    fields = ("title",)   # 限定现实的字段
    exclude = ("",)   # 不显示哪些字段，和fields相反
    ordering = ("nid",)  # 排序

    def patch_action(self, request, queryset):
        queryset.update(publishDate="2019-11-22")

    patch_action.short_description = "批量初始化"
    actions = [patch_action]


from django.contrib.admin.sites import AdminSite

admin.site.register(Book, BookConfig)
admin.site.register(Author)
admin.site.register(AuthorDetail)
admin.site.register(Publish)
