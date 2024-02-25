import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.append(PROJECT_ROOT)

import json
import re
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from description_parcer import params_description

def describer_dns(cat_name,driver):
    info = params_description.descriptor().category
    full_info = dict()
    full_name = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located(
                (By.CSS_SELECTOR, 'h1.product-card-top__title'))).text.lower()
    sh_specs = ''
    driver.find_element(By.CSS_SELECTOR, 'button.product-characteristics__expand').click()
    data = driver.find_element(By.CSS_SELECTOR, 'div.product-characteristics')
    time.sleep(0.5)
    params = data.find_elements(By.CSS_SELECTOR, 'div.product-characteristics__spec')
    for spec in params:
        spec_key = spec.find_element(By.CSS_SELECTOR,'div.product-characteristics__spec-title').text.lower()
        spec_val = spec.find_element(By.CSS_SELECTOR,'div.product-characteristics__spec-value').text.lower()
        sh_specs = f'{sh_specs}{spec_key}: {spec_val} | '
        full_info[spec_key] = spec_val
    sh_specs = sh_specs.removeprefix(' | ').lower().replace('\n', ' ')
    print(sh_specs)
    match cat_name:
        case 'cpu':
            if full_name.find('intel') != -1:
                info['author'] = 'intel'
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'celeron'])
                sockets = list(['lga 1151-v2', 'lga 1200', 'lga 1700', 'lga 2066'])
            else:
                info['author'] = 'amd'
                lines = list(
                    ['athlon', 'epyc', 'ryzen threadripper', 'ryzen 3',
                        'ryzen 5', 'ryzen 7', 'ryzen 9', 'fx'])
                sockets = list(['am3+', 'am4', 'am5', 'swrx8', 'tr4'])
            for line_name in lines:
                if full_name.find(line_name) != -1:
                    line = line_name
                    if full_name.find('ryzen') != -1 and full_name.find('pro') != -1:
                        line = f'{line_name} pro'
                    info['line'] = line
                    break
            for sckt in sockets:
                if sh_specs.find(sckt) != -1:
                    socket = sckt
                    info['socket'] = socket.replace('-', '')
            model = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['model'] = model
            cooler = re.search('(box[\w\W]* кулер)|(box)|(oem[\w\W]* кулер)', full_name)
            if cooler is not None:
                if cooler.group(1) is not None:
                    delivery_type = 'box'
                elif cooler.group(2) is not None:
                    delivery_type = 'box (без кулера)'
                else:
                    delivery_type = 'oem (с кулером)'
            else:
                delivery_type = 'oem'
            info['delivery_type'] = delivery_type
            boost_clock_frequency = re.search('частота в турбо режиме: нет', sh_specs)
            if boost_clock_frequency is None:
                boost_clock_frequency = re.search('частота в турбо режиме: [0-9]*.[0-9]*',
                                                    sh_specs).group().removeprefix('частота в турбо режиме ')
                info['boost_clock_frequency'] = boost_clock_frequency
            else:
                info['boost_clock_frequency'] = 'нет'
            info['clock_frequency'] = re.search('частота процессора: [0-9]*.[0-9]*|частота процессора: [0-9]*',
                                                sh_specs).group().removeprefix('частота процессора: ')
            info['core_number'] = re.search('количество ядер: [0-9]*', sh_specs).group().removeprefix(
                'количество ядер: ')
            info['threads_number'] = re.search('число потоков: [0-9]*', sh_specs).group().removeprefix(
                'число потоков: ')
            wattson = re.search('\(tdp\): [0-9]*', sh_specs).group().removeprefix('(tdp): ')
            info['tdp'] = wattson.strip()
            info['tech_process'] = re.search('[0-9]* нм', sh_specs).group().removesuffix(' нм')
            int_vd_core = re.search('интегрированное графическое ядро: есть', sh_specs)
            if int_vd_core is not None:
                info['integrated_video_core'] = \
                    re.search('модель графического процессора: [\w\W]* [|]', sh_specs).group().removeprefix(
                        'модель графического процессора: ').split(' |', maxsplit=1)[0]
            else:
                info['integrated_video_core'] = 'нет'
            print(info)
            return json.dumps(info), full_info
        case 'mb':
            full_name = full_name.removeprefix(
                'материнская плата ')
            info['author'] = full_name
            chipset = re.search('чипсет: amd [\w\W]*|чипсет: intel [\w\W]*', sh_specs).group().removeprefix(
                'чипсет ').removeprefix('amd ').removeprefix('intel ').split(' |', maxsplit=1)[0]
            info['chipset'] = chipset
            socket = \
                re.search('сокет [\w\W]* [|]', sh_specs).group().removeprefix('сокет ').split(' |', maxsplit=1)[
                    0]
            if socket is None:
                print(sh_specs)
                raise ValueError
            info['socket'] = socket
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_type_amount = re.search('количество слотов памяти: [0-9]*', sh_specs).group().removeprefix(
                'количество слотов памяти: ')
            info['memory_type_amount'] = int(memory_type_amount)
            form_factor = \
                re.search('форм-фактор: [\w\W]* [|]', sh_specs).group().removeprefix('форм-фактор: ').split(' |',
                                                                                                            maxsplit=1)[
                    0]
            info['form_factor'] = form_factor
            m2_amount = re.search('количество разъемов m.2: нет', sh_specs)
            if m2_amount is None:
                info['m2_amount'] = re.search('количество разъемов m.2: [0-9]*', sh_specs).group().removeprefix(
                    'количество разъемов m.2: ')
            else:
                info['m2_amount'] = 0
            print(info)
            return json.dumps(info), full_info
        case 'ram':
            full_name = full_name.removeprefix(
                'оперативная память ')
            author = re.search(
                'kingston|amd|patriot memory|netac|g.skill|pny|acer|adata|afox|agi|apacer|biwintech|cbr|corsair|crucial|digma|exegate|foxline|geil|gigabyte|hikvision|hp|hynix|infortrend|kimtigo|kingmax|kingspec|klevv|patriot|ocpc|qnap|qumo|samsung|silicon power|team|transcend|тми',
                full_name)
            info['author'] = author.group()
            memory_amount = re.search('всего комплекта: [0-9]*', sh_specs).group().removeprefix(
                'всего комплекта: ')
            info['memory_amount'] = memory_amount
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_frequency = re.search('[0-9]* мгц', sh_specs)
            info['memory_frequency'] = memory_frequency.group()
            is_kit = re.search('модулей в комплекте: 1', full_name)
            info['is_kit'] = 'нет' if is_kit is None else re.search('модулей в комплекте: [0-9]*',
                                                                    sh_specs).group().removeprefix(
                'модулей в комплекте: ')
            info['memory_speed'] = ''
            latency = re.search('\(cl\) [0-9]*', sh_specs).group().removeprefix('(cl): ')
            if latency is not None:
                info['latency'] = latency
            else:
                info['latency'] = ''
            is_XMP = re.search('xmp', sh_specs)
            info['is_XMP'] = False if is_XMP is None else True
            print(info)
            return json.dumps(info), full_info
        case 'gpu':
            full_name = full_name.removeprefix(
                'видеокарта ')
            author = re.search('(radeon)|(geforce|nvidia|quadro)|(intel)', full_name)
            if author is not None:
                if author.group(1) is not None:
                    info['author'] = 'amd'
                elif author.group(2) is not None:
                    info['author'] = 'nvidia'
                if author.group(3) is not None:
                    info['author'] = 'intel'
            info['model'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['video_card_author'] = full_name.split(' ')[0]
            info['memory_amount'] = re.search('объем видеопамяти: [0-9]*', sh_specs).group().removeprefix(
                'объем видеопамяти: ')
            info['interface'] = re.search('pci-e [0-9]*.[0-9]*', sh_specs).group()
            info['clock_frequency'] = re.search('работы видеочипа: [0-9]*', sh_specs).group().removeprefix(
                'работы видеочипа: ')
            memory_type = re.search('ddr[0-9]|gddr[0-9]x|gddr[0-9]|hbm2', sh_specs)
            info['memory_type'] = memory_type.group()
            info['memory_frequency'] = re.search('частота памяти: [0-9]*', sh_specs).group().removeprefix(
                'частота памяти: ')
            print(info)
            return json.dumps(info), full_info
        case 'ssd':
            info['author'] = \
                re.search('модель [\w\W]* [|]', sh_specs).group().removeprefix('модель ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            info['ssd_drive_capacity'] = re.search('объем накопителя: [0-9]*', sh_specs).group().removeprefix(
                'объем накопителя: ')
            info['purpose'] = 'внутренний'
            info['type'] = 'ssd'
            info['form_factor'] = re.search('m.2|2.5"|pci-e aic', sh_specs).group()
            info['interface'] = re.search('msata|sata 3|sata|pci-e xp[0-9]|pci-e [345].[0-9] x4|pci-e',
                                            sh_specs).group()
            info['nvme_support'] = re.search('nvme есть', sh_specs) is not None
            info['reading_speed'] = re.search('чтения: [0-9]*', sh_specs).group().removeprefix('чтения: ')
            info['writing_speed'] = re.search('записи: [0-9]*', sh_specs).group().removeprefix('записи: ')
            print(info)
            return json.dumps(info), full_info
        case 'hdd':
            info['author'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            info['hard_disk_capacity'] = re.search('объем hdd: [0-9]* [\w\W]{2}', sh_specs).group().removeprefix(
                'объем hdd: ')
            info['purpose'] = 'внутренний'
            info['type'] = 'hdd'
            info['form_factor'] = '3.5"'
            info['interface'] = re.search('sata iii', sh_specs).group()
            info['rotational_speed'] = re.search('[0-9]* об/мин', sh_specs).group().removesuffix(' об/мин')
            print(info)
            return json.dumps(info), full_info
        case 'spu':
            info['author'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            info['power'] = re.search('\(номинал\): [0-9]*', sh_specs).group().removeprefix('(номинал):')
            info['form_factor'] = re.search(
                'atx|sfx', sh_specs).group()
            info['fan_size'] = re.search('размеры вентиляторов: [0-9]*', sh_specs).group().removeprefix(
                'размеры вентиляторов: ')
            certificate = re.search('сертификат 80 plus: [\w\W]* [|]', sh_specs)
            info['certificate'] = \
                certificate.group().removeprefix('сертификат 80 plus: ').split(' |', maxsplit=1)[0]
            print(info)
            return json.dumps(info), full_info
        case 'pc_case':
            info['author'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            form_factor = re.search(
                'фактор совместимых плат: [\w\W]* [|]',
                sh_specs).group().removeprefix('фактор совместимых плат: ').split(' |', maxsplit=1)[0]
            info['form_factor'] = form_factor
            info['typesize'] = re.search('типоразмер корпуса: [\w\W]* [|]', sh_specs).group().removeprefix(
                'типоразмер корпуса: ').split(' |', maxsplit=1)[0]
            info['has_power_unit'] = re.search('встроенный бп: нет', sh_specs) is None
            info['is_window'] = re.search('окна на боковой стенке: нет', sh_specs) is None
            info['power_unit_position'] = \
                re.search('размещение блока питания: [\w\W]* [|]', sh_specs).group().removeprefix(
                    'размещение блока питания: ').split(' |', maxsplit=1)[0]
            max_gpu_length = re.search('длина устанавливаемой видеокарты: [0-9]*', sh_specs)
            if max_gpu_length is not None:
                info['max_gpu_length'] = max_gpu_length.group().removeprefix(
                    'длина устанавливаемой видеокарты: ')
            else:
                info['max_gpu_length'] = 0
            max_cpu_height = re.search('высота процессорного кулера: [0-9]*', sh_specs)
            if max_cpu_height is not None:
                info['max_cpu_height'] = max_cpu_height.group().removeprefix('высота процессорного кулера: ')
            else:
                info['max_cpu_height'] = 0
            print(info)
            return json.dumps(info), full_info
        case 'cool_cpu':
            info['author'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            info['model'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['socket'] = \
                re.search('сокет: [\w\W]* [|]', sh_specs).group().removeprefix('сокет: ').split(' |', maxsplit=1)[
                    0]
            info['fan_size'] = re.search('комплектных вентиляторов: [0-9]*', sh_specs).group().removeprefix(
                'комплектных вентиляторов: ')
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            tdp = re.search('[0-9]* вт', sh_specs)
            info['tdp'] = tdp.group().removesuffix(' вт')
            print(info)
            return json.dumps(info), full_info
        case 'cool_lck':
            info['author'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[
                    0].split(' ')[0]
            info['model'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['type_cooling'] = 'сво'
            info['socket'] = \
                re.search('сокет: [\w\W]* [|]', sh_specs).group().removeprefix('сокет: ').split(' |', maxsplit=1)[
                    0]
            info['fan_size'] = re.search('размеры вентиляторов: [0-9]*', sh_specs).group().removeprefix(
                'размеры вентиляторов: ')
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            print(info)
            return json.dumps(info), full_info
        case 'cool_case':
            info['author'] = full_name.removeprefix('комплект вентиляторов ').removeprefix('вентилятор ').split(' ')[0]
            info['model'] = full_name.removeprefix('комплект вентиляторов ').removeprefix('вентилятор ').split(' ', maxsplit=1)[1]
            info['fan_size'] = re.search('размер вентилятора: [0-9]*', sh_specs).group().removeprefix(
                'размер вентилятора: ')
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            print(info)
            return json.dumps(info), full_info