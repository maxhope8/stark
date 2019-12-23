from django.forms import ModelForm

from starkapp.service.stark import site, ModelStark
from app01.models import *


class BookModelForm(ModelForm):
    class Meta:
        model = Book
        fields = "__all__"
        error_messages = {
            "title": {'required': '不能为空'},
            "price": {'required': '不能为空'},
        }


# 自定义配置类
class BookStark(ModelStark):
    list_display = ["nid", "title", "price", "publish", "authors"]
    list_display_link = ["nid", "title"]
    search_fields = ["title", "price"]
    model_form_class = BookModelForm
    list_filter = ["authors", "publish", "title"]

    def patch_list(self, queryset):
        queryset = queryset

    patch_list.desc = "显示"
    actions = [patch_list]


site.register(Book, BookStark)
site.register(Publish)
site.register(Author)
site.register(AuthorDetail)
