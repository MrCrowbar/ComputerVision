import numpy as np
import urllib.request
import os
import time
from socket import error as SocketError
import errno
from urllib.error import URLError, HTTPError
import cv2
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

#import urllib2
from multiprocessing.dummy import Pool as ThreadPool

"""
Actividad integradora2 Computer Vision
Se maneja multithreading para agilizar el proceso de los URLS.
"""


resp = ''
respList = []

def urlHandler(url):
  global removeCount
  global globalCount
  try:
      resp = urllib.request.urlopen(url,data=None,timeout=2)
      respList.append(resp)
  except:
      removeCount += 1
  globalCount += 1
  progress = int(globalCount*100/listSize)
  print('\rCurrent progress: ',progress,'%. ','Removed items: ',removeCount,end='')

fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.set_headless()
driver = webdriver.Firefox(options=fireFoxOptions)
driver.implicitly_wait(15)


#def test_search_in_python_org(self):
while True:
    pool = ThreadPool(15)
    #Buscar la palabra ingresada
    userWord = input('Ingresa una palabra a buscar: ')
    print('Buscando la palabra ', userWord,'...')
    
    driver.get("http://image-net.org/index")
    elem = driver.find_element_by_name("q")
    elem.send_keys(userWord)
    elem.send_keys(Keys.RETURN)

    #Buscar los resultados arrojados
    urlLocation = driver.find_element_by_class_name('search_result') #Tabla de resultados
    if not urlLocation.is_displayed():
        print("No hay resultados para: ",userWord)
        userQuit = input("Quieres buscar otra palabra? --> ")
        if userQuit in ['yes','YES','y','Y']:
            continue
        else:
            break
    else:
        wnid = urlLocation.find_element_by_tag_name('a') #Elegimos el link que nos lleve al árbol de resultados
        wnid.click()

        #Buscar en el arbol de contenido
        print('Buscando la palabra ', userWord, ' en el árbol de resultados...')
        tree = driver.find_element_by_id('tree')
        myClick = tree.find_elements_by_class_name('jstree-open') #Encontramos todas las hojas abiertas del árbol
        synsetoffset = myClick[-1].get_attribute('synsetoffset') #Vamos a la última hoja que es en dónde se encuentra lo que buscamos
        synsetoffset = 'n' + synsetoffset #Creamos el wnind
        downloadLink = 'http://www.image-net.org/api/text/imagenet.synset.geturls?wnid=' + synsetoffset #Nos vamos directo a los URLs
        folderPathTrain = './trainPARALEL/' + userWord + '/'
        folderPathTest = './testPARALEL/' + userWord + '/'
        try:
            os.makedirs(folderPathTrain)
            print('Created folder ',folderPathTrain)
        except FileExistsError:
            print(folderPathTrain,' already exists')

        try:
            os.makedirs(folderPathTest)
            print('Created folder ',folderPathTest)
        except FileExistsError:
            print(folderPathTest,' already exists')

        #Descargar URLS a archivo de texto
        print('Descargando URLS a la carpeta ',folderPathTrain, ' y ',folderPathTest)
        driver.get(downloadLink)
        try:
            content = driver.find_element_by_tag_name('pre').get_attribute('innerText')
        except:
            print("Error, going to beginning")
        else:
            urlList = list(content.split('\n'))
            urlList.pop()
            urlList.pop()
            newList = urlList[:500]
            listSize = len(newList)
            print('Original list size: ', str(listSize))
            progress = 0
            resp = ''
            img = ''
            filePath = ''
            globalCount = 0
            writeCount = 0
            removeCount = 0
            respList = []
            print('Cleaning and verifying URLs')
            start_time = time.time()
            results = pool.map(urlHandler, newList)
            print('\nTime taken: ',time.time() - start_time)
            pool.close()
            pool.join()
            listSize -= removeCount
            print(listSize)

            #LIMPIAR IMAGENES
            print('Cleaning images')
            globalCount = 0
            removeCount = 0
            imgList = []
            for resp in respList:
                try:
                    imgByte = np.asarray(bytearray(resp.read()),dtype='uint8')
                    img = cv2.imdecode(imgByte, cv2.IMREAD_COLOR)
                except:
                    removeCount += 1
                else:
                    try:
                        if img.any() == None:
                            pass
                    except:
                        removeCount += 1
                    else:
                        cv2.imshow('Image', img)
                        cv2.waitKey(1)
                        imgList.append(img)

                globalCount += 1
                progress = int(globalCount*100/listSize)
                print('\rCurrent progress: ',progress,'%. ','Removed items: ',removeCount,end='')
            cv2.destroyAllWindows()

            listSize = len(imgList)
            print('\nFinal imgSize: ', listSize)
            
            #GUARDAR IMAGNES
            trainningSize = int(80*listSize/100)
            testingSize = int(20*listSize/100)
            print('Training size: ',trainningSize, '. Testing size: ',testingSize)

            writeCount = 0
            for img in imgList[:testingSize]:
                filePath = userWord + '_' + str(writeCount) + '.png'
                cv2.imwrite(folderPathTest+filePath, img)
                writeCount += 1
                progress = int(writeCount*100/testingSize)
                #print('\rCurrent progress: ',progress,'%. ','Written items: ',writeCount,end='')
            print('Testing written images: ', writeCount)

            writeCount = 0
            for img in imgList[testingSize:]:
                filePath = userWord + '_' + str(writeCount) + '.png'
                cv2.imwrite(folderPathTrain+filePath, img)
                writeCount += 1
                progress = int(writeCount*100/trainningSize)
                #print('\rCurrent progress: ',progress,'%. ','Written items: ',writeCount,end='')
            print('Trainning written images: ', writeCount)
            
        userQuit = input("Quieres buscar otra palabra? --> ")
        if userQuit in ['yes','y','YES','Y']:
            continue
        else:
            print('Shutting down driver')
            driver.close()
            break

