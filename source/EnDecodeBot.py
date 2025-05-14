import telebot
from collections import Counter
from heapq import heappush, heappop

# Инициализация бота
bot = telebot.TeleBot('TOKEN')

# Словарь для хранения состояний пользователей
user_states = {}

# Функция шифрования методом Цезаря
def caesar_encrypt(text, shift):
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('а') if char.lower() in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' else ord('a')
            is_upper = char.isupper()
            char = chr((ord(char.lower()) - ascii_offset + shift) % 26 + ascii_offset)
            result += char.upper() if is_upper else char
        else:
            result += char
    return result

# Функция дешифрования методом Цезаря
def caesar_decrypt(text, shift):
    return caesar_encrypt(text, -shift)

# Функция кодирования Шеннона-Фано
def shannon_fano_encode(text):
    # Подсчет частот символов
    freq = Counter(text)
    codes = {}
    
    def divide(items):
        if len(items) <= 1:
            return
        
        total = sum(freq[item] for item in items)
        half = total / 2
        current = 0
        
        for i, item in enumerate(items):
            if current >= half:
                break
            current += freq[item]
            
        left = items[:i]
        right = items[i:]
        
        for item in left:
            codes[item] = codes.get(item, '') + '0'
        for item in right:
            codes[item] = codes.get(item, '') + '1'
            
        divide(left)
        divide(right)
    
    divide(sorted(freq.keys(), key=lambda x: freq[x], reverse=True))
    
    encoded = ''.join(codes[char] for char in text)
    return encoded, codes

# Функция кодирования Хэмминга (7,4)
def hamming_encode(data):
    result = ""
    for i in range(0, len(data), 4):
        chunk = data[i:i+4]
        if len(chunk) < 4:
            chunk = chunk.ljust(4, '0')
        
        d1, d2, d3, d4 = map(int, chunk)
        
        # Вычисление контрольных битов
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        
        # Формирование закодированного блока
        encoded = f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}"
        result += encoded
        
    return result

# Функция декодирования Шеннона-Фано
def shannon_fano_decode(encoded_text, codes):
    # Создаем обратный словарь для декодирования
    reverse_codes = {v: k for k, v in codes.items()}
    
    result = ""
    current_code = ""
    
    for bit in encoded_text:
        current_code += bit
        if current_code in reverse_codes:
            result += reverse_codes[current_code]
            current_code = ""
            
    return result

# Функция декодирования Хэмминга (7,4)
def hamming_decode(encoded_data):
    result = ""
    binary_result = ""
    
    # Разбиваем на блоки по 7 бит
    for i in range(0, len(encoded_data), 7):
        chunk = encoded_data[i:i+7]
        if len(chunk) < 7:
            break
            
        # Извлекаем информационные биты
        d1 = int(chunk[2])
        d2 = int(chunk[4])
        d3 = int(chunk[5])
        d4 = int(chunk[6])
        
        # Добавляем информационные биты в результат
        binary_result += f"{d1}{d2}{d3}{d4}"
    
    # Преобразуем бинарную последовательность в текст
    for i in range(0, len(binary_result), 16):  # Изменено с 8 на 16 для поддержки Unicode
        if i + 16 <= len(binary_result):
            byte = binary_result[i:i+16]
            result += chr(int(byte, 2))
    
    return result

# Функция для автоматического взлома шифра Цезаря
def crack_caesar(text):
    # Частоты букв в русском языке (в порядке убывания)
    russian_freq = {
        'о': 0.1097, 'е': 0.0845, 'а': 0.0801, 'и': 0.0735, 'н': 0.0670,
        'т': 0.0626, 'с': 0.0547, 'р': 0.0473, 'в': 0.0454, 'л': 0.0440,
        'к': 0.0349, 'м': 0.0321, 'д': 0.0298, 'п': 0.0281, 'у': 0.0262,
        'я': 0.0201, 'ы': 0.0198, 'з': 0.0165, 'ь': 0.0144, 'б': 0.0140,
        'г': 0.0130, 'ч': 0.0121, 'й': 0.0106, 'х': 0.0097, 'ж': 0.0094,
        'ш': 0.0073, 'ю': 0.0064, 'ц': 0.0048, 'щ': 0.0036, 'э': 0.0032,
        'ф': 0.0026, 'ъ': 0.0004, 'ё': 0.0004
    }
    
    # Определяем язык текста
    is_russian = any(c.lower() in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for c in text)
    
    if is_russian:
        alphabet = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        freq_dict = russian_freq
    else:
        alphabet = 'abcdefghijklmnopqrstuvwxyz'
        # Частоты букв в английском языке
        freq_dict = {
            'e': 0.1270, 't': 0.0906, 'a': 0.0817, 'o': 0.0751, 'i': 0.0697,
            'n': 0.0675, 's': 0.0633, 'h': 0.0609, 'r': 0.0599, 'd': 0.0425,
            'l': 0.0403, 'c': 0.0278, 'u': 0.0276, 'm': 0.0241, 'w': 0.0236,
            'f': 0.0223, 'g': 0.0202, 'y': 0.0197, 'p': 0.0193, 'b': 0.0149,
            'v': 0.0098, 'k': 0.0077, 'j': 0.0015, 'x': 0.0015, 'q': 0.0010,
            'z': 0.0007
        }
    
    # Подсчитываем частоты букв в зашифрованном тексте
    text_freq = {}
    total_letters = 0
    for char in text.lower():
        if char in alphabet:
            text_freq[char] = text_freq.get(char, 0) + 1
            total_letters += 1
    
    # Нормализуем частоты
    for char in text_freq:
        text_freq[char] /= total_letters
    
    # Находим сдвиг с минимальной разницей между частотами
    best_shift = 0
    min_diff = float('inf')
    
    for shift in range(len(alphabet)):
        diff = 0
        for char in text_freq:
            if char in alphabet:
                # Находим соответствующую букву в эталонном распределении
                idx = alphabet.index(char)
                shifted_idx = (idx - shift) % len(alphabet)
                shifted_char = alphabet[shifted_idx]
                if shifted_char in freq_dict:
                    diff += abs(text_freq[char] - freq_dict[shifted_char])
        
        if diff < min_diff:
            min_diff = diff
            best_shift = shift
    
    # Расшифровываем текст с найденным сдвигом
    decrypted = caesar_decrypt(text, best_shift)
    
    return decrypted, best_shift

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот для шифрования/дешифрования сообщений.\n"
                         "Доступные команды:\n"
                         "/caesar_encrypt - шифрование методом Цезаря\n"
                         "/caesar_decrypt - дешифрование методом Цезаря\n"
                         "/crack_caesar - автоматический взлом шифра Цезаря\n"
                         "/shannon_fano - кодирование методом Шеннона-Фано\n"
                         "/shannon_fano_decode - декодирование методом Шеннона-Фано\n"
                         "/hamming - кодирование методом Хэмминга\n"
                         "/hamming_decode - декодирование методом Хэмминга")

# Обработчик команды шифрования Цезаря
@bot.message_handler(commands=['caesar_encrypt'])
def handle_caesar_encrypt(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_text'}
    bot.reply_to(message, "Пожалуйста, введите текст для шифрования:")

# Обработчик для получения текста
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_text')
def handle_caesar_text(message):
    user_id = message.from_user.id
    user_states[user_id]['text'] = message.text
    user_states[user_id]['state'] = 'waiting_for_shift'
    bot.reply_to(message, "Теперь введите сдвиг (целое число):")

# Обработчик для получения сдвига
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_shift')
def handle_caesar_shift(message):
    user_id = message.from_user.id
    try:
        shift = int(message.text)
        text = user_states[user_id]['text']
        result = caesar_encrypt(text, shift)
        bot.reply_to(message, f"Зашифрованный текст: {result}")
        del user_states[user_id]  # Очищаем состояние пользователя
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите корректное целое число для сдвига.")
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при шифровании. Попробуйте снова.")
        del user_states[user_id]

# Обработчик команды дешифрования Цезаря
@bot.message_handler(commands=['caesar_decrypt'])
def handle_caesar_decrypt(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_decrypt_text'}
    bot.reply_to(message, "Пожалуйста, введите текст для дешифрования:")

# Обработчик для получения текста для дешифрования
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_decrypt_text')
def handle_caesar_decrypt_text(message):
    user_id = message.from_user.id
    user_states[user_id]['text'] = message.text
    user_states[user_id]['state'] = 'waiting_for_decrypt_shift'
    bot.reply_to(message, "Теперь введите сдвиг (целое число):")

# Обработчик для получения сдвига для дешифрования
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_decrypt_shift')
def handle_caesar_decrypt_shift(message):
    user_id = message.from_user.id
    try:
        shift = int(message.text)
        text = user_states[user_id]['text']
        result = caesar_decrypt(text, shift)
        bot.reply_to(message, f"Расшифрованный текст: {result}")
        del user_states[user_id]  # Очищаем состояние пользователя
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введите корректное целое число для сдвига.")
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при дешифровании. Попробуйте снова.")
        del user_states[user_id]

# Обработчик команды кодирования Шеннона-Фано
@bot.message_handler(commands=['shannon_fano'])
def handle_shannon_fano(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_shannon_text'}
    bot.reply_to(message, "Пожалуйста, введите текст для кодирования методом Шеннона-Фано:")

# Обработчик для получения текста для Шеннона-Фано
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_shannon_text')
def handle_shannon_fano_text(message):
    user_id = message.from_user.id
    try:
        text = message.text
        encoded, codes = shannon_fano_encode(text)
        bot.reply_to(message, f"Закодированный текст: {encoded}\nТаблица кодов: {codes}")
        del user_states[user_id]  # Очищаем состояние пользователя
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при кодировании. Попробуйте снова.")
        del user_states[user_id]

# Обработчик команды кодирования Хэмминга
@bot.message_handler(commands=['hamming'])
def handle_hamming(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_hamming_text'}
    bot.reply_to(message, "Пожалуйста, введите текст для кодирования методом Хэмминга:")

# Обработчик для получения текста для Хэмминга
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_hamming_text')
def handle_hamming_text(message):
    user_id = message.from_user.id
    try:
        text = message.text
        # Преобразуем текст в бинарную последовательность (16 бит на символ для Unicode)
        binary = ''.join(format(ord(c), '016b') for c in text)
        encoded = hamming_encode(binary)
        bot.reply_to(message, f"Закодированный текст (Хэмминг): {encoded}")
        del user_states[user_id]
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при кодировании. Попробуйте снова.")
        del user_states[user_id]

# Обработчик команды декодирования Шеннона-Фано
@bot.message_handler(commands=['shannon_fano_decode'])
def handle_shannon_fano_decode(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_shannon_decode_text'}
    bot.reply_to(message, "Пожалуйста, введите закодированный текст:")

# Обработчик для получения закодированного текста Шеннона-Фано
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_shannon_decode_text')
def handle_shannon_fano_decode_text(message):
    user_id = message.from_user.id
    user_states[user_id]['encoded_text'] = message.text
    user_states[user_id]['state'] = 'waiting_for_shannon_codes'
    bot.reply_to(message, "Теперь введите таблицу кодов в формате: {'символ': 'код', ...}")

# Обработчик для получения кодов Шеннона-Фано
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_shannon_codes')
def handle_shannon_fano_codes(message):
    user_id = message.from_user.id
    try:
        encoded_text = user_states[user_id]['encoded_text']
        codes = eval(message.text)  # Преобразуем строку в словарь
        decoded_text = shannon_fano_decode(encoded_text, codes)
        bot.reply_to(message, f"Декодированный текст: {decoded_text}")
        del user_states[user_id]
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при декодировании. Убедитесь, что формат таблицы кодов правильный.")
        del user_states[user_id]

# Обработчик команды декодирования Хэмминга
@bot.message_handler(commands=['hamming_decode'])
def handle_hamming_decode(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_hamming_decode'}
    bot.reply_to(message, "Пожалуйста, введите закодированный текст (последовательность битов):")

# Обработчик для получения закодированного текста Хэмминга
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_hamming_decode')
def handle_hamming_decode_text(message):
    user_id = message.from_user.id
    try:
        encoded_text = message.text.replace(" ", "")
        if not all(c in '01' for c in encoded_text):
            bot.reply_to(message, "Ошибка: введенный текст должен содержать только 0 и 1")
            del user_states[user_id]
            return
            
        decoded_text = hamming_decode(encoded_text)
        if decoded_text:
            bot.reply_to(message, f"Декодированный текст: {decoded_text}")
        else:
            bot.reply_to(message, "Не удалось декодировать текст. Проверьте правильность ввода.")
        del user_states[user_id]
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при декодировании. Убедитесь, что введен корректный закодированный текст.")
        del user_states[user_id]

# Обработчик команды взлома шифра Цезаря
@bot.message_handler(commands=['crack_caesar'])
def handle_crack_caesar(message):
    user_id = message.from_user.id
    user_states[user_id] = {'state': 'waiting_for_crack_text'}
    bot.reply_to(message, "Пожалуйста, введите зашифрованный текст для автоматического взлома:")

# Обработчик для получения текста для взлома
@bot.message_handler(func=lambda message: message.from_user.id in user_states and 
                    user_states[message.from_user.id]['state'] == 'waiting_for_crack_text')
def handle_crack_text(message):
    user_id = message.from_user.id
    try:
        text = message.text
        decrypted, shift = crack_caesar(text)
        bot.reply_to(message, f"Найденный сдвиг: {shift}\nРасшифрованный текст: {decrypted}")
        del user_states[user_id]
    except Exception as e:
        bot.reply_to(message, "Произошла ошибка при взломе шифра. Попробуйте снова.")
        del user_states[user_id]

# Запуск бота
bot.polling()
