from unittest.mock import Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Screen, ScreenNotAccessible


class ScreenTests(TestCase):
        def setUp(self):
            self.s = Screen(name="test", ipaddress="10.0.1.9",
                            password="TEST")
            self.s.save()
            self.user = User.objects.create_user('js', 'js@localhost', 'test')
            self.user.save()

        def test_fetch1(self):
            xdict = \
              {'type': 'ImageContent',
               'name': 'wales5',
               'duration': 10,
               'last_display': 'Wed May 24 10:40:15 2017',
               'installed': 'Wed May 24 10:40:15 2017',
               'hash': b'\x03\x1e\xdd}Ae',
               'expire': '',
               'display_count': 200,
               'display_restrictions': {},
               'file': '/home/pi/csscreen/screen_content_cache/cardiffrun.png',
               }
            self.s._remote_call = Mock(return_value={
             'status': 'success',
             'content': [xdict]
            })
            r = self.s.fetch_current()
            self.assertEqual(len(r), 1)
            self.assertDictEqual(r[0], xdict)
            self.assertEqual(self.s._update_status, "success")
            self.assertEqual(self.s._cache, [xdict])
            self.assertIsNotNone(self.s.lastfetch)

        def test_fetch_fail(self):
            # erturn vablue status=failure raise ScreenNotAccessible
            # also can get requests.RequestException (parent of
            # several other exceptions)
            self.s._remote_call = Mock(side_effect=ScreenNotAccessible())
            with self.assertRaises(ScreenNotAccessible):
                r = self.s.fetch_current()

            self.s._remote_call = Mock(return_value={
                'status': 'failure',
                'content': []
            })
            with self.assertRaises(ScreenNotAccessible):
                self.s.fetch_current()

        def test_index(self):
            c = Client()
            # not logged in; should redirect to login
            response = c.get(reverse('screen-list'), follow=True)
            self.assertRedirects(response, reverse('login')+'?next=/')
            self.assertTemplateUsed(response, 'registration/login.html')
            c.login(username='js', password='test')
            response = c.get(reverse('screen-list'))
            self.assertTemplateUsed(response, 'screens/screen_list.html')
            self.assertQuerysetEqual(response.context['screens'],
                                     [repr(self.s)])
