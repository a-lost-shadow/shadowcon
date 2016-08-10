from django.conf.urls import url

from convention.views import games, user

app_name = 'convention'
urlpatterns = [
    url(r'^games/description/$', games.ListGameView.as_view(), name='games_list'),
    url(r'^games/edit/(?P<pk>[0-9]+)/$', games.UpdateGameView.as_view(), name='edit_game'),
    url(r'^games/register/$', games.NewGameView.as_view(), name='submit_game'),
    url(r'^games/schedule/$', games.ScheduleView.as_view(), name='show_schedule'),
    url(r'^games/schedule/edit/$', games.ScheduleEditView.as_view(), name='edit_schedule'),
    url(r'^games/schedule/ajax/view/location/$', games.SchedulerHandler.as_view(), name='ajax_location_schedule_view'),
    url(r'^user/attendance/$', user.AttendanceView.as_view(), name='register_attendance'),
    url(r'^user/payment/$', user.PaymentView.as_view(), name='payment'),
    url(r'^user/new/$', user.NewUserView.as_view(), name='new_user'),
    url(r'^user/profile/$', user.show_profile, name='user_profile'),
    url(r'^attendance/list/$', user.AttendanceList.as_view(), name='attendance_list')
]
