# pdb off
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import numpy as np
import wave
import sys


def firstSearch(wav):
    wav.setpos(0)
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()

    # 1920 сэмплов <=> 40 мс <=> длительность 1 импульса при частоте дискретизации 48000
    # Здесь с помощью "грубого" поиска определяется момент времемни начала преамбулы звукового сигнала -
    # два последовательных тональных импульса с частотой несущей ~5105 Гц. Для этого производится последовательная выборка
    # по 2000 сэмплов, на которой вычисляется fft и определяется частота, соответствующая максимуму мощности в спектре,
    # затем она сравнивается с искомым значением (5105 Гц)
    n = 2000
    while True:
        data = wav.readframes(n)
        samples = np.fromstring(data, dtype=types[sampwidth])
        y = np.abs(rfft(samples))
        x = rfftfreq(n, 1 / framerate)

        y_max = y[0]
        x_max = x[0]
        for i in range(len(y)):
            if y[i] > y_max:
                y_max = y[i]
                x_max = x[i]

        preamble_freqs = 5105
        found = False
        if np.abs(preamble_freqs - x_max) < 200:
            found = True
            break

        # print(f"Found freq {preamble_freqs} at sample_pos {wav.tell() - (n / 2)}")
        # print(f"local maximum of freq is {x_max}\n")
        if wav.tell() > 100000:
            print("Cannot find any signal")
            return -1, -1

    return int(wav.tell() - (n / 2)), preamble_freqs


# Функция принимает набор частот и амплитуд вычисленного преобразования Фурье;
# возвращает частоту, соответствующую максимуму мощности в переданном спектре
# Чтобы исключить попадание НЧ составляющей высокого уровня выставлено ограничение диапазона поиска для частоты: f > 750 Гц
def searchMaxFreq(x, y):
    x = [i for i in x if i > 750]
    y = y[len(y) - len(x) :]
    y_max = y[0]
    x_max = x[0]
    for i in range(len(y)):
        if y[i] > y_max:
            y_max = y[i]
            x_max = x[i]
    # print(f"Resolved max freq is {x_max}")
    return x_max


# Функция принимает значение частоты и определяет, к какой частоте из набора частот протокола "Алисы"
# (т.е. какому сообщению из ансамбля) соответствовала бы переданная частота
def compareFreqToExist(tmp_f):
    global frequencies
    freqs = frequencies.keys()
    min_difference = 10e9
    ans_f = 10e9
    for f in freqs:
        if np.abs(f - tmp_f) < min_difference:
            min_difference = np.abs(f - tmp_f)
            ans_f = f
    # print(f"Freq {tmp_f} is similar to {ans_f}")
    return ans_f


# Функция принимает значение момента времени (позицию курсора в файле <=> номер текущего сэмпла) и текующую частоту тона;
# В качестве результата возвращает позицию (номер сэмпла), обозначающую конец данного тонального импульса
def searchTact(wav, start_pnt, detected_f):
    wav.setpos(start_pnt)
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()

    curr_f = detected_f

    n = 100
    while True:
        data = wav.readframes(n)
        samples = np.fromstring(data, dtype=types[sampwidth])
        y = rfft(samples)
        x = rfftfreq(n, 1 / framerate)
        tmp_f = searchMaxFreq(x, np.abs(y))
        tmp_f = compareFreqToExist(tmp_f)
        # print(f"on sample {wav.tell() - n} - {tmp_f}")
        if curr_f != tmp_f:
            wav.setpos(wav.tell() - n)
            return wav.tell()
        else:
            continue


# По заданной позиции (номеру сэмпла) вычисляет мгновенный спектр (по fft) в правой полуокрестности заданной точки
def countFFT(wav, start):
    n = 1000
    wav.setpos(start)
    data = wav.readframes(n)
    samples = np.fromstring(data, dtype=types[sampwidth])
    y = rfft(samples)
    x = rfftfreq(n, 1 / framerate)
    return x, np.abs(y)


# Функция анализирует wav файл и переводит значения частот тональных импульсов (элементарных сообщений) в 16-чный код
def encoding(wav, code):
    global frequencies
    (nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()

    while True and (wav.tell() < nframes - 2000):
        wav.setpos(wav.tell() + 400)

        # print(f"Curr pos is {wav.tell()}")
        x, y = countFFT(wav, wav.tell())
        central_f = compareFreqToExist(searchMaxFreq(x, y))
        code.append(frequencies[central_f])
        # print(f"{central_f} - {frequencies[central_f]}")

        wav.setpos(wav.tell() + 520)


# Функция переводит 16-чный код, полученный при анализе спектра сообщения, в символы кодировки ascii, выделяя из них информативную часть
# о значении параметров ssid и password и возвращает их значения
def resolveCode(code):
    # resolve ssid length
    ans = []
    type_of_synh = True  # переключатель типа синхронизации: True - 3, False - 2
    curr_sym = []
    curr_sym.append(code.pop(0))
    curr_sym.append(code.pop(0))
    ssid_len = int("".join(curr_sym), 16)
    ans.append(ssid_len)
    # print(ssid_len)

    # read first 3 symbols
    for i in range(3):
        curr_sym = []
        curr_sym.append(code.pop(0))
        curr_sym.append(code.pop(0))
        if len(ans) == ssid_len + 1:
            pass_len = int("".join(curr_sym), 16)
            ans.append(pass_len)
        else:
            current = bytearray.fromhex("".join(curr_sym)).decode()
            ans.append(current)

    k = 5
    while True:
        if k == 5:
            if type_of_synh:
                curr_sym = []
                curr_sym.append(code.pop(0))
                for i in range(4):
                    code.pop(0)
                curr_sym.append(code.pop(0))
                # print(f"curr_sym is {curr_sym}")

                if len(ans) == ssid_len + 1:
                    pass_len = int("".join(curr_sym), 16)
                    ans.append(pass_len)
                else:
                    current = bytearray.fromhex("".join(curr_sym)).decode()
                    ans.append(current)

            else:
                for i in range(4):
                    code.pop(0)
            type_of_synh = not type_of_synh
            k = 0
        elif k < 5:
            curr_sym = []
            curr_sym.append(code.pop(0))
            curr_sym.append(code.pop(0))
            # print(f"curr_sym is {curr_sym}")

            if len(ans) == ssid_len + 1:
                pass_len = int("".join(curr_sym), 16)
                ans.append(pass_len)
            else:
                current = bytearray.fromhex("".join(curr_sym)).decode()
                ans.append(current)
            k += 1

            if ("".join(curr_sym) == "10") and (len(ans) == ssid_len + pass_len + 3):
                ans.pop()
                break

    # print(*ans)

    ssid_len = int(ans.pop(0))
    ssid = "".join(ans[0:ssid_len])
    ans = ans[ssid_len:]
    pass_len = int(ans.pop(0))
    password = "".join(ans)

    # print(f"\nssid is {ssid}")
    # print(f"password is {password}\n")

    return ssid, password


# ----------------------------------------------------------------------------------------------------------------------------------------------------------------------
types = {1: np.int8, 2: np.int16, 4: np.int32}

frequencies = {
    1025: "0",
    1280: "1",
    1535: "2",
    1790: "3",
    2045: "4",
    2300: "5",
    2555: "6",
    2810: "7",
    3065: "8",
    3320: "9",
    3575: "a",
    3830: "b",
    4085: "c",
    4340: "d",
    4595: "e",
    4850: "f",
    5105: "!",
    5625: "!!",
    6200: "!!!",
}

path = input("Write path to .wav file: ")

wav = wave.open(path, mode="r")
(nchannels, sampwidth, framerate, nframes, comptype, compname) = wav.getparams()

# функция "ищет" преамбулу пакета
start_pnt, detected_f = firstSearch(wav)
if start_pnt == -1:
    sys.exit(0)

final_start_point = searchTact(wav, start_pnt, detected_f)

# print(f"Final start point is {final_start_point}")

# пропуск 4 оставшихся синхроимпульсов
wav.setpos(wav.tell() + 1920 * 4)
info_begin = wav.tell()
# print(wav.tell())

code = []
symbols = []

encoding(wav, code)
ssid, password = resolveCode(code)

print(f"\nssid is {ssid}")
print(f"password is {password}\n")
