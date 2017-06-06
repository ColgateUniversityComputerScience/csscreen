from unittest.mock import Mock
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Screen, ScreenNotAccessible


class ScreenTests(TestCase):
        def setUp(self):
            self.s = Screen(name="test", ipaddress="10.0.1.18",
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


        def test_index2(self):
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
                 'file': '/home/pi/csscreen/screen_content_cache/cardiffrun.png'}
            # self.s._remote_call = Mock(return_value={
            #     'status': 'success',
            #     'content': [xdict]
            # })
            self.s_remote_call = Mock(return_value={
                'content': {'display_items': 1}, 'status': 'success'})
            c = Client()
            c.login(username='js', password='test')
            response = c.get(reverse('screen-list'))
            self.assertTemplateUsed(response, 'screens/screen_list.html')
            self.assertQuerysetEqual(response.context['screens'],
                                     [repr(self.s)])

        def test_upload_content(self):
            c = Client()
            c.login(username='js', password='test')
            postcontent = {'content_name': 'blah',
                           'duration': 10,
                           'xexcept': 'M:0000-0100,T:0100-0200,W:0200-0300',
                           'xonly': '',
                           'expire': '',
                           'url': 'http://cs.colgate.edu',
                           'screen': '1',
                           'action': 'url'}
            response = c.post(reverse('screencontent-update'), postcontent)
            # success results in 302 redirect to /
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('screen-detail', args=[1]))
            self.assertIn("Screen test update successful",
                          c.cookies['messages'].value)

            postcontent = {'content_name': 'blah',
                           'duration': 10,
                           'xexcept': 'X:0001-0002',
                           'xonly': '',
                           'expire': '',
                           'url': 'http://cs.colgate.edu',
                           'screen': '1',
                           'action': 'url'}
            response = c.post(reverse('screencontent-update'), postcontent)
            self.assertTemplateUsed("screens/screen_content_update.html")
            self.assertContains(response, "constraint string X:0001-0002.  Should be in the format")

            postcontent = {'content_name': 'test blah',
                           'duration': 10,
                           'xexcept': '',
                           'xonly': '',
                           'expire': '',
                           'url': 'http ://cs.colgate.edu',
                           'screen': '1',
                           'action': 'url'}
            response = c.post(reverse('screencontent-update'), postcontent)
            self.assertTemplateUsed("screens/screen_content_update.html")
            self.assertContains(response, "Enter a valid value.")

        def test_delete_content(self):
            c = Client()
            c.login(username='js', password='test')
            response = c.get(reverse('screencontent-delete',
                                     args=[self.s.id, 'notexist']))
            self.assertRedirects(response, reverse('screen-detail', args=[1]))
