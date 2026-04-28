from django.contrib import admin

from .models import Badge, Category, Event, EventCategory, Participation, Review, UserBadge

admin.site.register(Event)
admin.site.register(Category)
admin.site.register(EventCategory)
admin.site.register(Participation)
admin.site.register(Review)
admin.site.register(Badge)
admin.site.register(UserBadge)