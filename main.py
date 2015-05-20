__version__ = '1.0'
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture

import numpy
import array
import android
import os
from nfc import CreateNfcBeamUrisCallback
import fnmatch
import io


from jnius import autoclass, cast
from jnius import JavaClass
from jnius import PythonJavaClass

mContext = autoclass('android.content.Context')
PythonActivity = autoclass('org.renpy.android.PythonActivity')
activity = PythonActivity.mActivity
Intent = autoclass('android.content.Intent')
mEnvironment = autoclass('android.os.Environment')
Uri = autoclass('android.net.Uri')
Builder.load_file('main.kv')


class HomeScreen(Screen):
	from threading import *
	mMediaStore = autoclass('android.provider.MediaStore')
	mFile = autoclass('java.io.File')
	

	def likeMore(self):
		self.ids.button1.text = self.ids.button1.text+"!"
	def AndroidTest(self):
		vibrator = activity.getSystemService(mContext.VIBRATOR_SERVICE)
		if 'ANDROID_ROOT' in os.environ:
			vibrator.vibrate(3000)	
		else:
			print 'not android?'
			print os.environ
	
	def startCamera(self):

		#intention = Intent(self.mMediaStore.ACTION_VIDEO_CAPTURE)
		intention = Intent(self.mMediaStore.INTENT_ACTION_VIDEO_CAMERA)
		self.con = cast(mContext, activity)			
		intention.resolveActivity(self.con.getPackageManager())	
		if intention.resolveActivity( self.con.getPackageManager()) != None:
			activity.startActivityForResult(intention,1)
	ButtonNumber = 0
	def addVideo(self):
		wid = FileWidget()
		wid.setName('Name %d' % self.ButtonNumber)
		self.ButtonNumber = self.ButtonNumber+1
		self.ids.fileList.add_widget(wid)


	def printDir(self):	
		DCIMdir = mEnvironment.getExternalStoragePublicDirectory(mEnvironment.DIRECTORY_DCIM)
		print DCIMdir.list()
	
	def getStoredMedia(self):
		DCIMdir = mEnvironment.getExternalStoragePublicDirectory(mEnvironment.DIRECTORY_DCIM)
		print DCIMdir.toURI().getPath()	
		self.ids.fileList.clear_widgets()
		for root, dirnames, filenames in os.walk(DCIMdir.getAbsolutePath()):
			for filename in fnmatch.filter(filenames,'*.mp4'):
				wid = FileWidget()
				wid.setName(filename)
				wid.setUri(root+'/'+filename)
				#wid.makeThumbnail()
				self.ids.fileList.add_widget(wid)
				

class CameraScreen(Screen):
	mMediaStore = autoclass('android.provider.MediaStore')
	def startCamera(self):

		intention = Intent(self.mMediaStore.ACTION_VIDEO_CAPTURE)
		self.con = cast(mContext, activity)			
		intention.resolveActivity(self.con.getPackageManager())	
		if intention.resolveActivity( self.con.getPackageManager()) != None:
			activity.startActivityForResult(intention,1)

class NfcScreen(Screen):
	def printDir(self):	
		DCIMdir = mEnvironment.getExternalStoragePublicDirectory(mEnvironment.DIRECTORY_DCIM)
		print DCIMdir.list()


class FileWidget(BoxLayout):

	mBitmap = autoclass("android.graphics.Bitmap")
	mCompressFormat = autoclass("android.graphics.Bitmap$CompressFormat")
	mThumbnailUtils = autoclass ("android.media.ThumbnailUtils")
	mByteArrayOutputStream = autoclass ("java.io.ByteArrayOutputStream")
	mArrays = autoclass("java.util.Arrays")
	#mThumbnails = autoclass("android.provider.MediaStore.Video.Thumbnails")
	name = 'NO FILENAME SET'
	uri = None
	thumbnail = None  #Gotta make a default for this later
	MICRO_KIND = 3
	FULL_KIND = 2
	MINI_KIND = 1
	def setName(self, nom):
		self.name = nom
		self.ids.filebutton.text = nom
	def setUri(self,ur):
		self.uri = ur
	def setThumb(self,thumb):
		self.thumbnail = thumb
	def pressed(self):
		print self.uri
		self.makeThumbnail()
	def switchFormats(self, pixels):
		print pixels[0]
		#b = bytearray()
		#b.append(pixels[0])		
		print format('B', str(pixels[0]))
		return pixels
	def makeThumbnail(self):
		out = self.mByteArrayOutputStream()
		'THUMBNAIL'		
		self.thumbnail = self.mThumbnailUtils.createVideoThumbnail(self.uri,self.MICRO_KIND)
		tex = Texture.create(size=(self.thumbnail.getWidth(),self.thumbnail.getHeight()) , colorfmt= 'rgba', bufferfmt='int')
		#pixels = array('i', [0] *self.thumbnail.getWidth() * self.thumbnail.getHeight())
		pixels = [0] *self.thumbnail.getWidth() * self.thumbnail.getHeight()
		
		self.thumbnail.getPixels(pixels, 0,self.thumbnail.getWidth(),0,0,self.thumbnail.getWidth(), self.thumbnail.getHeight())
		#pixels = b''.join(map(chr, pixels))		
		#print pixels
		#pixels = array.array('B',pixels).tostring()		
		pixels = numpy.asarray(pixels)		
		tex.blit_buffer(pixels, colorfmt = 'rgba', bufferfmt = 'int')
		print "OLD PIXELS!"		
		print pixels
		self.ids.img.texture = tex
		self.ids.img.canvas.ask_update()

		print 'COMPRESSION'		
		#self.thumbnail.compress(self.mCompressFormat.valueOf("JPEG"), 100, out)
	
		print 'GONNA PRINT THE STREAM'		
		print out
		print 'GONNA PRINT THE BYTEARRAY!'
		print 'it has length %d', out.size()
		print out.toByteArray()
		print 'DID I PRINT IT? GONNA READ IT IN	'
		#outstr = self.mArrays.toString(out.toByteArray())
		#ba = bytearray()
		#ba.extend(outstr)
		print "printed bytearray"
		#self.ids.img.texture = CoreImage(io.BytesIO(ba), ext='jpg')
		print 'THUMBNAIL BUDDY'
		print self.uri
		print self.thumbnail
		


class Skelly(App):
	sm = ScreenManager()
	history = []
	HomeScr = HomeScreen(name='home')
	NfcScr = NfcScreen(name='nfc')
	sm.switch_to(HomeScr)

	def build(self):
		android.map_key(android.KEYCODE_BACK,1001)
		win = Window
		win.bind(on_keyboard=self.key_handler)

		self.provider = CreateNfcBeamUrisCallback()
		self.HomeScr.getStoredMedia()
		return self.sm

	def swap_to(self, Screen):
		self.history.append(self.sm.current_screen)
		self.sm.switch_to(Screen, direction='left')


	def on_pause(self):
		return True
	def on_stop(self):
		pass
	def on_resume(self):
		self.HomeScr.getStoredMedia()
	def key_handler(self,window,keycode1, keycode2, text, modifiers):
		if keycode1 in [27,1001]:
			if len(self.history ) != 0:
				print self.history
				self.sm.switch_to(self.history.pop(), direction = 'right')				
			else:
				App.get_running_app().stop()

if __name__== '__main__':
	Skelly().run()
