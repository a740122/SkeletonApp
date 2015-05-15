__version__ = '1.0'
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.lang import Builder
import android
import os


from jnius import autoclass, cast
from jnius import JavaClass
from jnius import PythonJavaClass

mContext = autoclass('android.content.Context')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
activity = PythonActivity.mActivity
Intent = autoclass('android.content.Intent')
mEnvironment = autoclass('android.os.Environment')
  
Builder.load_file('main.kv')


class HomeScreen(Screen):
	mMediaStore = autoclass('android.provider.MediaStore')
	def likeMore(self):
		self.ids.button1.text = self.ids.button1.text+"!"
	def AndroidTest(self):
		vibrator = activity.getSystemService(mContext.VIBRATOR_SERVICE)
		#vibrator.vibrate(10000)
		if 'ANDROID_ROOT' in os.environ:
			vibrator.vibrate(10000)	
		else:
			print 'not android?'
			print os.environ
	
	def startCamera(self):

		intention = Intent(self.mMediaStore.ACTION_VIDEO_CAPTURE)
		self.con = cast(mContext, PythonActivity.mActivity)			
		intention.resolveActivity(self.con.getPackageManager())	
		if intention.resolveActivity( self.con.getPackageManager()) != None:
			activity.startActivityForResult(intention,1)

class CameraScreen(Screen):
	mMediaStore = autoclass('android.provider.MediaStore')
	def startCamera(self):

		intention = Intent(self.mMediaStore.ACTION_VIDEO_CAPTURE)
		self.con = cast(mContext, PythonActivity.mActivity)			
		intention.resolveActivity(self.con.getPackageManager())	
		if intention.resolveActivity( self.con.getPackageManager()) != None:
			activity.startActivityForResult(intention,1)
	#def on_resume(self):
	#	root.manager.current='home'
class NfcScreen(Screen):
	mNfcAdapter = autoclass('android.nfc.NfcAdapter')
	#mIO = autoclass('java.io')
	mFile = autoclass('java.io.File')
	def printDir(self):	
		DCIMdir = mEnvironment.getExternalStoragePublicDirectory(mEnvironment.DIRECTORY_DCIM)
		print DCIMdir.list()


sm = ScreenManager()
sm.add_widget(HomeScreen(name='home'))
sm.add_widget(CameraScreen(name="cam"))
sm.add_widget(NfcScreen(name='nfc'))



class Skelly(App):
	def build(self):
		android.map_key(android.KEYCODE_BACK,1001)
		win = Window
		win.bind(on_keyboard=self.key_handler)
		return sm

	def on_pause(self):
		return True
	def on_stop(self):
		pass
	def on_resume(self):
		pass
	def key_handler(self,window,keycode1, keycode2, text, modifiers):
		if keycode1 in [27,1001]:
			if(sm.current!='home'):
				sm.current = 'home'
			else:
				App.get_running_app().stop()

if __name__== '__main__':
	Skelly().run()
