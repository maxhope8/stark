import copy

from django.conf.urls import url
from django.db.models import ForeignKey, ManyToManyField
from django.forms import ModelForm
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models.fields.related import ManyToManyField
from django.forms.models import ModelChoiceField


class ModelStark(object):
    list_display = ["__str__"]
    list_display_link = []
    model_form_class = None
    search_fields = []
    actions = []
    list_filter = []

    def __init__(self, model, site):
        self.model = model
        self.site = site
        self.model_name = self.model._meta.model_name
        self.app_label = self.model._meta.app_label

    # 使用modelform组件
    def get_modelfrom_class(self):
        # from django.forms import widgets as wid
        class ModelFormClass(ModelForm):
            class Meta:
                model = self.model
                fields = "__all__"
                # 这样的字段就限定死了，所以我们这里不能这样使用
                # widgets = {
                #     "title": wid.TextInput(attrs={"class": "form-control"})
                # }
        if not self.model_form_class:
            return ModelFormClass
        else:
            return self.model_form_class

    # 展示编辑连接
    def edit_link(self, obj=None, is_header=False):
        if is_header:
            return "操作"
        name = "{}_{}_change".format(self.app_label, self.model_name)
        return mark_safe("<a href=%s>编辑</a>" % reverse(name, args=(obj.pk,)))

    # 原本都是在用户自己的配置类中写，但是现在写入modelStark中是因为，是因为每个表可能都能用到，减少代码重复
    def delete_link(self, obj=None, is_header=False):
        if is_header:
            return "操作"
        name = "{}_{}_delete".format(self.app_label, self.model_name)
        return mark_safe("<a href=%s>删除</a>" % reverse(name, args=(obj.pk,)))

    def select_btn(self, obj=None, is_header=None):
        if is_header:
            return mark_safe("<input id='mutPut' type='checkbox'>")
        return mark_safe("<input type='checkbox' value=%s name='_selected_action'>" % obj.pk)

    # 获取反向解析的name
    def get_edit_url(self, obj):
        edit_url = "{}_{}_change".format(self.app_label, self.model_name)
        return edit_url

    def get_delete_url(self, obj):
        delete_url = "{}_{}_delete".format(self.app_label, self.model_name)
        return delete_url

    def get_add_url(self):
        add_url = "{}_{}_add".format(self.app_label, self.model_name)
        return add_url

    def get_list_url(self):
        list_url = "{}_{}_list".format(self.app_label, self.model_name)
        return list_url

    @property
    def get_list_display(self):
        new_list_display = []
        new_list_display.extend(self.list_display)
        # 如果设置了list_display_link就把编辑删除
        if not self.list_display_link:
            new_list_display.append(ModelStark.edit_link)
        new_list_display.append(ModelStark.delete_link)
        new_list_display.insert(0, ModelStark.select_btn)

        return new_list_display

    # 获取filter的查询条件的Q对象
    @property
    def get_filter_condition(self):
        from django.db.models import Q
        filter_condition = Q()
        for field, val in self.request.GET.items():
            # 过滤非list_filter的值，因为page在里面，加进去之后，查询条件是and，模型中没有报错
            if field in self.list_filter:
                filter_condition.children.append((field, val))
        return filter_condition

    @property
    def get_search_condition(self):
        from django.db.models import Q
        search_condition = Q()
        search_condition.connector = "or"  # 设置关系为或
        if self.search_fields:  # ["title", "price"]
            key_word = self.request.GET.get("q", None)
            # 如果有值才添加，没有纸就直接返回空的Q()
            self.key_word = key_word
            if key_word:
                for search_field in self.search_fields:
                    # 因为条件设置得是or所以这里才可以成立，如果是and，全部遍历加进去查询可能会出错
                    search_condition.children.append((search_field + "__contains", key_word))
        return search_condition

    # 首页展示页面
    def change_list(self, request):
        if request.method == "POST":
            func_name = request.POST.get("action")
            # getlist多个值处理
            pk_list = request.POST.getlist("_selected_action")
            queryset = self.model.objects.filter(pk__in=pk_list)
            func = getattr(self, func_name)
            func(queryset=queryset)
        self.request = request
        add_url = self.get_add_url()
        # search模糊查询
        queryset = self.model.objects.filter(self.get_search_condition)
        # filter模糊查询
        queryset = queryset.filter(self.get_filter_condition)
        cl = ChangeList(self, request, queryset)

        return render(request, "index.html", locals())

    # 批量删除
    def patch_delete(self, queryset):
        queryset.delete()
        return redirect(self.get_list_url())
    patch_delete.desc = "批量删除"

    def get_actions(self):
        temp = []
        temp.extend(self.actions)
        temp.append(ModelStark.patch_delete)
        return temp

    def add(self, request):
        modelform = self.get_modelfrom_class()
        from django.forms.boundfield import BoundField
        form = modelform()
        for field in form:
            print(type(field.field))
            if isinstance(field.field, ModelChoiceField):
                field.is_pop = True
                related_model_name = field.field.queryset.model._meta.model_name
                related_app_name = field.field.queryset.model._meta.app_label
                _url = reverse("{}_{}_add".format(related_app_name, related_model_name)) + \
                       "?pop_res_id=id_{}".format(field.name)
                field.url = _url
        if request.method == "GET":
            return render(request, "add_index.html", locals())
        else:
            data = request.POST
            form = modelform(data=data)
            if form.is_valid():
                obj = form.save()
                pop_res_id = request.GET.get("pop_res_id")
                if pop_res_id:
                    res = {"pk": obj.pk, "text": str(obj), "pop_res_id": pop_res_id}
                    return render(request, "pop.html", {"res": res})
                else:
                    return redirect(self.get_list_url())
            else:
                return render(request, "add_index.html", locals())

    def delete(self, request, id):
        del_obj = self.model.objects.filter(nid=id).first()
        if request.method == "GET":
            list_url = self.get_list_url()
            # 为什么要确认页面，是因为重要数据需要二次确认，防止误删
            return render(request, "del_index.html", locals())
        else:
            del_obj.delete()
            return redirect(self.get_list_url())

    # 编辑页面
    def change(self, request, id):
        form = self.get_modelfrom_class()
        obj = self.model.objects.filter(pk=id).first()
        if request.method == "GET":
            form = form(instance=obj)
            return render(request, "change_index.html", locals())
        else:
            form = form(data=request.POST, instance=obj)
            if form.is_valid():
                form.save()
                return redirect(self.get_list_url())
            else:
                return render(request, "change_index.html", locals())

    def get_urls_2(self):
        temp = []
        model_name = self.model._meta.model_name  # 当前模型表
        app_label = self.model._meta.app_label  # 当前app

        temp.append(url(r"^add/$", self.add, name="%s_%s_add" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/delete/$", self.delete, name="%s_%s_delete" % (app_label, model_name)))
        temp.append(url(r"^(\d+)/change/$", self.change, name="%s_%s_change" % (app_label, model_name)))
        temp.append(url(r"^$", self.change_list, name="%s_%s_list" % (app_label, model_name)))
        return temp

    @property
    def urls_2(self):
        return self.get_urls_2(), None, None  # [], None, None


class ChangeList(object):
    def __init__(self, config, request, queryset):
        self.config = config
        self.request = request
        self.queryset = queryset

        from starkapp.util.paginator import Pagination
        current_page = request.GET.get("page")
        all_count = self.queryset.count()
        base_url = self.request.path_info
        params = self.request.GET
        paginator = Pagination(current_page, all_count, base_url, params)
        data_list = self.queryset[paginator.start: paginator.end]
        self.paginator = paginator
        self.data_list = data_list
        # actions 批量操作的动作
        self.actions = self.config.get_actions()
        # filter  过滤的字段
        self.list_filter = self.config.list_filter

    def get_filter_link_tag(self):
        link_list = {}
        data = self.request.GET
        import copy
        params = copy.deepcopy(data)
        for filter_field_name in self.config.list_filter:
            # 为什么放里面而不是放外面
            data = self.request.GET
            import copy
            params = copy.deepcopy(data)

            current_id = self.request.GET.get(filter_field_name, 0)
            filter_field_obj = self.config.model._meta.get_field(filter_field_name)
            # filter_field = FilterField(filter_field_name, filter_field_obj, self)
            if isinstance(filter_field_obj, ManyToManyField) or isinstance(filter_field_obj, ForeignKey):
                data_list = filter_field_obj.related_model.objects.all()
            else:
                data_list = self.config.model.objects.values_list("pk", filter_field_name)
            temp = []
            # 处理全部标签
            if params.get(filter_field_name, None):
                del params[filter_field_name]
                temp.append("<a href='?%s'>全部</a>" % (params.urlencode()))
            else:
                temp.append("<a class='active' href='?%s'>全部</a>" % (params.urlencode()))
            # 处理数据标签
            for obj in data_list:
                if isinstance(filter_field_obj, ManyToManyField) or isinstance(filter_field_obj, ForeignKey):
                    pk, text = obj.pk, str(obj)
                    params[filter_field_name] = pk
                else:
                    pk, text = obj
                    params[filter_field_name] = text
                _url = params.urlencode()
                if current_id == str(pk) or current_id == text:
                    link_tag = "<a class='active' href='?%s'>%s</a>" % (_url, text)  # %s/%s/
                else:
                    link_tag = "<a href='?%s'>%s</a>" % (_url, text)  # %s/%s/
                temp.append(link_tag)
            link_list[filter_field_name] = temp
        # ff = FilterField(self.config, self.request)
        # link_list = ff.get_filter_link()
        return link_list

    def handler_action(self):
        temp = []
        for action in self.actions:
            temp.append({"name": action.__name__, "desc": action.desc if getattr(action, "desc", None) else action.__name__})
        return temp

    def get_header(self):
        header_list = []
        # 这里的代码是处理表头数据的
        for field in self.config.get_list_display:
            if callable(field):
                val = field(self.config, is_header=True)
                header_list.append(val)
            else:
                if field == "__str__":
                    header_list.append(self.config.model._meta.model_name.upper())
                else:
                    field_obj = self.config.model._meta.get_field(field)
                    header_list.append(field_obj.verbose_name)
        return header_list

    def get_body(self):
        data_list = self.data_list
        new_data_list = []
        # 这里才是我们数据库中的数据
        for obj in data_list:
            temp = []
            for field in self.config.get_list_display:
                if callable(field):
                    val = field(self.config, obj)
                else:
                    try:
                        field_obj = self.config.model._meta.get_field(field)
                        # 对于多对多字段的现实进行处理
                        if isinstance(field_obj, ManyToManyField):
                            val = getattr(obj, field).all()
                            val = ",".join([str(item) for item in val])
                        else:
                            val = getattr(obj, field)
                            # 如果有list_display_link，就把他编程a标签
                            if field in self.config.list_display_link:
                                val = mark_safe("<a href=%s>%s</a>" % (reverse(self.config.get_edit_url(obj), args=(obj.pk,)), val))
                    except Exception as e:
                        val = getattr(obj, field)
                temp.append(val)
            new_data_list.append(temp)
        return new_data_list


# 针对((),()),[[],[]]数据类型构建a标签
"""class LinkTagGen(object):
    def __init__(self, data, filter_field, request):
        self.data = data
        self.filter_field = filter_field
        self.request = request

    def __iter__(self):
        current_id = self.request.GET.get(self.filter_field.filter_field_name, 0)
        params = copy.deepcopy(self.request.GET)
        params._mutable = True
        if params.get(self.filter_field.filter_field_name):
            del params[self.filter_field.filter_field_name]
            _url = "%s?%s" % (self.request.path_info, params.urlencode())
            yield mark_safe("<a href='%s'>全部</a>" % _url)
        else:
            _url = "%s?%s" % (self.request.path_info, params.urlencode())
            yield mark_safe("<a href='%s' class='active'>全部</a>" % _url)
        for item in self.data:
            if self.filter_field.filter_field_obj.choices:
                pk, text = str(item[0], item[1])
            elif isinstance(self.filter_field.filter_field_obj, ForeignKey) or \
                isinstance(self.filter_field.filter_field_obj, ManyToManyField):
                pk, text = str(item.pk), item
            else:
                pk, text = item[1], item[1]
            params[self.filter_field.filter_field_name] = pk
            _url = "%s?%s" % (self.request.path_info, params.urlencode())
            if current_id == pk:
                link_tag = "<a href='%s' class='active'>%s</a>" % (_url, text)
            else:
                link_tag = "<a href='%s'>%s</a>" % (_url, text)
            yield mark_safe(link_tag)"""


# 为每一个过滤的字段封装成整体类
class FilterField(object):
    def __init__(self, config, request):
        self.config = config
        self.request = request

    def get_data(self):
        if isinstance(self.filter_field_obj, ForeignKey) or isinstance(self.filter_field_obj, ManyToManyField):
            return self.filter_field_obj.related_model.objects.all()
        elif self.filter_field_obj.choices:
            return self.filter_field_obj.choices
        else:
            return self.config.model.objects.values_list("pk", self.filter_field_name)

    def get_params(self):
        data = self.request.GET
        import copy
        params = copy.deepcopy(data)
        return params

    def get_filter_link(self):
        link_list = {}
        for filter_field_name in self.config.list_filter:
            self.filter_field_name = filter_field_name
            # 为什么放里面而不是放外面
            params = self.get_params()
            current_id = self.get_current_id()
            self.get_filter_field_obj()
            temp = self.get_link_list(params, current_id)
            link_list[filter_field_name] = temp
        return link_list

    def get_current_id(self):
        current_id = self.request.GET.get(self.filter_field_name, 0)
        return current_id

    def get_filter_field_obj(self):
        filter_field_obj = self.config.model._meta.get_field(self.filter_field_name)
        self.filter_field_obj = filter_field_obj

    def get_link_list(self, params, current_id):
        data_list = self.get_data()
        temp = []
        temp = self.deal_all_tag(params, temp)
        temp = self.deal_data_tag(params, data_list, current_id, temp)
        return temp

    def deal_data_tag(self, params, data_list, current_id, temp):
        for obj in data_list:
            pk, text, params = self.get_pk_text(params, obj)
            _url = params.urlencode()
            if current_id == str(pk) or current_id == text:
                link_tag = "<a class='active' href='?%s'>%s</a>" % (_url, text)  # %s/%s/
            else:
                link_tag = "<a href='?%s'>%s</a>" % (_url, text)  # %s/%s/
            temp.append(link_tag)
        return temp

    def get_pk_text(self, params, obj):
        if isinstance(self.filter_field_obj, ManyToManyField) or isinstance(self.filter_field_obj, ForeignKey):
            pk, text = obj.pk, str(obj)
            params[self.filter_field_name] = pk
        else:
            pk, text = obj
            params[self.filter_field_name] = text
        return pk, text, params

    def deal_all_tag(self, params, temp):
        if params.get(self.filter_field_name, None):
            del params[self.filter_field_name]
            temp.append("<a href='?%s'>全部</a>" % (params.urlencode()))
        else:
            temp.append("<a class='active' href='?%s'>全部</a>" % (params.urlencode()))
        return temp


class StarkSite(object):

    def __init__(self):
        self._registry = {}

    def register(self, model, stark_class=None, **options):
        if not stark_class:
            # 如果注册的时候没有自定义配置类，执行
            stark_class = ModelStark   # 配置类

        # 降配置类对象加到_registry字典中，建立模型类
        self._registry[model] = stark_class(model, self)   # _registry={'model':stark_class(model)}

    def get_urls(self):
        """构造一层url"""
        temp = []
        for model, stark_class_obj in self._registry.items():
            # model:一个模型表
            # stark_class_obj:当前模型表相应的配置类对象
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            # 分发增删改查url,问什么要是用stark_class_obj.urls_2,因为我们需要使用每个类定制的内容，如list_display
            # 如果将urls_2还是放入StarkSite中那么，每个模型的现实都是一样的，我们根本没有用到定制显示的参数
            temp.append(url(r"^%s/%s/" % (app_label, model_name), stark_class_obj.urls_2))
            """
               path('app01/user/',UserConfig(User,site).urls2),
               path('app01/book/',ModelStark(Book,site).urls2),
            """
        return temp

    @property
    def urls(self):
        return self.get_urls(), None, None


site = StarkSite()
