# YaAlisaCrack script

В данной работе представлена программа для расшифрования данных, передаваемых в виде акустического сигнала по протоколам Яндекс.Станции.
За основу взята следующая статья https://habr.com/ru/articles/469435/.
Работа не является продолжением вышеуказанной статьи.

### Технологии

- python
- пакеты python из файла requirements.txt
- make

### Структура

```shell
.
└── WAV-examples/
    ├── abcdef_0123456789_noise.wav
    ├── abcdef_0123456789.wav
    ├── ABCDEF_9876543210.wav
    ├── jfk3sFGbfoe__99jenu6_67.wav
    ├── Thd_56jj__k0gypod9.wav
    └── with_noise.wav
├── Handbook.docx
├── Makefile
├── README.md
├── requirements.txt
├── main.py
```

### Подготовка и запуск

#### Установка

- установить python в вашей ОС
- установить make в вашей ОС
- склонировать репозиторий

#### Запуск

- при первом запуске (для настройки проекта и запуска): запустить `make launch`
- при последующих запусках: `make run`

Далее следует приглашение в консоли ввести путь до .wav-файла
`Write path to .wav file:`

Ввод осуществляется относительно текущей директории, образцы располагаются в папке WAV-examples. Пример ввода для анализа файла `with_noise.wav`:
`./WAV-examples/with_noise.wav`


#### Формат имени .wav файлов:

`ABCDEF_9876543210.wav` означает `ssid:ABCDEF` , `password:9876543210`

### Ссылки

- документация Python: https://docs.python.org/3/
- документация matplotlib: https://matplotlib.org/stable/index.html
- документация numpy: https://numpy.org/doc/
- документация scipy: https://docs.scipy.org/doc/scipy/