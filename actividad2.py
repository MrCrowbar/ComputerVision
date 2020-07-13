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

#Función para verificar URLs mediante multithreading
def urlHandler(url):
  global removeCount
  global globalCount
  try:
      response = urllib.request.urlopen(url,data=None,timeout=2)
      responseList.append(response)
  except:
      removeCount += 1
  globalCount += 1
  progress = int(globalCount*100/listSize)
  print('\rProgreso actual: ',progress,'%. ','Items removidos: ',removeCount,end='')

#Elegir el webdriver para Selenium
fireFoxOptions = webdriver.FirefoxOptions()
fireFoxOptions.headless = True
driver = webdriver.Firefox(options=fireFoxOptions)
driver.implicitly_wait(15)


while True:
    #Buscar la palabra ingresada
    userWord = input('Ingresa una palabra a buscar: ')
    print('Buscando la palabra ', userWord,' en Image net...')
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
        folderPathTrain = './train/' + userWord + '/'
        folderPathTest = './test/' + userWord + '/'
        try:
            os.makedirs(folderPathTrain)
            print('Carpeta ',folderPathTrain,' creada')
        except FileExistsError:
            print(folderPathTrain,' ya existe')

        try:
            os.makedirs(folderPathTest)
            print('Carpeta ',folderPathTest,' creada')
        except FileExistsError:
            print(folderPathTest,' ya existe')

        #Descargar URLS a archivo de texto
        print("Iniciando obtención de imágenes")
        driver.get(downloadLink)
        try:
            content = driver.find_element_by_tag_name('pre').get_attribute('innerText')
        except:
            print("Error, volviendo al inicio")
        else:
            urlList = list(content.split('\n'))
            listSize = len(urlList)
            print('Tamaño de lista original: ', str(listSize))
            progress = 0
            img = ''
            filePath = ''
            globalCount = 0
            removeCount = 0
            responseList = []
            print('Descartando y verificando URLs con multithreading')
            threads = int(input("ENTER NUMBER OF THREADS--TESTING PURPOSE: "))
            start_time = time.time()
            pool = ThreadPool(threads)
            pool.map(urlHandler, urlList)
            pool.close()
            pool.join()
            print("\nEXECUTION TIME--TESTING PURPOSE: ", round(time.time() - start_time,2),' seconds')

            #LIMPIAR IMAGENES
            print('Verificando imágenes')
            globalCount = 0
            removeCount = 0
            imgList = []
            for response in responseList:
                try:
                    imgByte = np.asarray(bytearray(response.read()),dtype='uint8')
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
                        imgList.append(img)

                globalCount += 1
                progress = int(globalCount*100/listSize)
                print('\rProgreso actual: ',progress,'%. ','Items removidos: ',removeCount,end='')
            listSize = len(imgList)
            print('\nTamaño de lista con elementos válidos: ', listSize)
            
            #GUARDAR IMAGNES
            trainningSize = int(80*listSize/100)
            testingSize = int(20*listSize/100)
            print('Elementos de entrenamiento: ',trainningSize, '. Elementos de testing: ',testingSize)
            writeCount = 0
            for img in imgList[:testingSize]:
                filePath = userWord + '_' + str(writeCount) + '.png'
                cv2.imwrite(folderPathTest+filePath, img)
                writeCount += 1
            print('Imágenes de testing guardadas en la carpeta ',folderPathTest)

            writeCount = 0
            for img in imgList[testingSize:]:
                filePath = userWord + '_' + str(writeCount) + '.png'
                cv2.imwrite(folderPathTrain+filePath, img)
                writeCount += 1
            print('Imágenes de entrenamiento guardadas en la carpeta ',folderPathTrain)

        userQuit = input("Quieres buscar otra palabra? --> ")
        if userQuit in ['yes','y','YES','Y']:
            continue
        else:
            print('Cerrando driver...')
            driver.close()
            break