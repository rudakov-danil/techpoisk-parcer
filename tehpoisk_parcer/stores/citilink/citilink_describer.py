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

def describer_citilink(cat_name, driver):
    info = params_description.descriptor().category
    full_info = dict()
    full_name = driver.find_element(By.CSS_SELECTOR, 'h1.app-catalog-tn2wxd').text.lower()
    WebDriverWait(driver, 10).until(
                expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, 'button.app-catalog-1wmowf6'))).click()
    time.sleep(0.5)
    params = driver.find_elements(By.CSS_SELECTOR, 'div.app-catalog-xc0ceg')
    sh_specs = ''
    for spec in params:
        spec_key = spec.find_element(By.CSS_SELECTOR,'span.app-catalog-1eqtzki').text
        spec_val = spec.find_element(By.CSS_SELECTOR,'span.app-catalog-1uhv1s4').text
        sh_specs = f'{sh_specs}{spec_key}: {spec_val} | '
        full_info[spec_key] = spec_val
    sh_specs = sh_specs.removeprefix(' | ').lower()
    print(sh_specs)
    match cat_name:
        case 'cpu':
            if full_name.find('intel') != -1:
                info['author'] = 'intel'
            else:
                info['author'] = 'amd'
            info['line'] = re.search('поколение процессоров: [\w\W]* [|]', sh_specs).group().removeprefix(
                'поколение процессоров: ').split(' |', maxsplit=1)[0]
            info['model'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['socket'] = \
                re.search('сокет: [\w\W]* [|]', sh_specs).group().removeprefix('сокет: ').split(' |', maxsplit=1)[
                    0]
            info['delivery_type'] = \
                re.search('тип поставки: [\w\W]* [|]', sh_specs).group().removeprefix('тип поставки: ').split(
                    ' |',
                    maxsplit=1)[
                    0]
            clock = re.search('([0-9]*.[0-9]* ггц и [0-9]*.[0-9]*)|([0-9]*.[0-9]* ггц)', sh_specs)
            if clock is not None:
                if clock.group(1) is not None:
                    clock_frequency = float(clock.group(1).split(' ггц')[0])
                    boost_clock_frequency = float(clock.group(1).split('и ')[1])
                else:
                    clock_frequency = float(clock.group(2).split(' ггц')[0])
                    boost_clock_frequency = 0
            else:
                clock_frequency = 0
                boost_clock_frequency = 0
            info['clock_frequency'] = int(clock_frequency * 1000)
            info['boost_clock_frequency'] = int(boost_clock_frequency * 1000)
            wattson = re.search('[0-9]* вт', sh_specs).group().removesuffix(' вт')
            info['tdp'] = wattson
            techprocess = re.search('[0-9]* нм', sh_specs).group().removesuffix(' нм')
            info['tech_process'] = techprocess.strip()
            info['core_number'] = re.search('количество ядер: [0-9]*', sh_specs).group().removeprefix(
                'количество ядер: ')
            info['threads_number'] = re.search('количество потоков: [0-9]*', sh_specs).group().removeprefix(
                'количество потоков: ')
            integrated_video_core = re.search('встроенное графическое ядро: есть', sh_specs)
            if integrated_video_core is not None:
                info['integrated_video_core'] = \
                    re.search('модель графического ядра [\w\W]* [|]', sh_specs).group().removeprefix(
                        'модель графического ядра ').split(' |', maxsplit=1)[0]
            info['core'] = \
                re.search('ядро: [\w\W]* [|]', sh_specs).group().removeprefix('ядро: ').split(' |', maxsplit=1)[0]
            print(info)
            return json.dumps(info), full_info
        case 'mb':
            info['author'] = \
                re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                    0]
            chipset = \
                re.search('чипсет: [\w\W]* [|]', sh_specs).group().removeprefix('чипсет: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['chipset'] = chipset
            socket = re.search('гнездо процессора: [\w\W]* [|]', sh_specs).group().removeprefix(
                'гнездо процессора: ').split(' |', maxsplit=1)[0]
            info['socket'] = socket
            memory_type = re.search('ddr[0-9]', sh_specs).group()
            info['memory_type'] = memory_type
            memory_type_amount = \
                re.search("слотов памяти ddr[0-9] [0-9]*", sh_specs).group().rsplit(' ', maxsplit=1)[1]
            info['memory_type_amount'] = memory_type_amount
            info['form_factor'] = \
                re.search('форм-фактор: [\w\W]* [|]', sh_specs).group().removeprefix('форм-фактор: ').split(' |',
                                                                                                            maxsplit=1)[
                    0]
            m2_amount = re.search('разъемов m.2: [0-9]*', sh_specs)
            if m2_amount is None:
                m2_amount = 0
            else:
                m2_amount = m2_amount.group().removeprefix('разъемов m.2: ')
            info['m2_amount'] = m2_amount
            print(info)
            return json.dumps(info), full_info
        case 'ram':
            author = re.search(
                'kingston|amd|patriot memory|patriot|netac|g.skill|acer|a-data|afox|agi|apacer|biwintech|cbr|corsair|crucial|digma|exegate|foxline|geil|gigabyte|hikvision|hp|hyxis|infortrend|kimtigo|kingmax|kingspec|ocpc|qnap|qumo|samsung|silicon power|team group|terramaster|thermaltake|transcend|тми',
                full_name)
            info['author'] = author.group()
            memory_amount = re.search('объем модуля: [0-9]*', sh_specs).group().removeprefix('объем модуля: ')
            is_kit = re.search('количество модулей: [0-9]*', sh_specs)
            if is_kit is not None:
                info['memory_amount'] = int(memory_amount) * int(
                    is_kit.group().removeprefix('количество модулей: '))
                info['is_kit'] = is_kit.group().removeprefix('количество модулей: ')
            else:
                info['memory_amount'] = int(memory_amount)
                info['is_kit'] = 'нет'
            memory_type = re.search('ddr[0-9]|ddr[0-9]l', full_name)
            info['memory_type'] = memory_type.group()
            info['memory_frequency'] = re.search('скорость: [0-9]*', sh_specs).group().removeprefix('скорость: ')
            info['memory_speed'] = ''
            info['latency'] = re.search('cl[0-9]*').group()
            info['is_XMP'] = False
            print(info)
            return json.dumps(info), full_info
        case 'gpu':
            info['author'] = re.search('nvidia|amd|intel', full_name).group()
            info['model'] = \
                re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['video_card_author'] = full_name.split(' ')[0]
            info['memory_amount'] = re.search('[0-9]* гб|[0-9]*гб', full_name).group().removesuffix(
                ' гб').removesuffix('гб')
            info['interface'] = re.search('интерфейс подключения: [\w\W]* [|]', sh_specs).group().removeprefix(
                'интерфейс подключения: ').split(' |', maxsplit=1)[0]
            info['clock_frequency'] = \
                re.search('частота графического процессора: [\w\W]* [|]', sh_specs).group().removeprefix(
                    'частота графического процессора: ').split(' |', maxsplit=1)[0]
            info['memory_type'] = re.search('ddr[0-9]|gddr[0-9]x|gddr[0-9]|hbm2', sh_specs).group()
            info['memory_frequency'] = re.search('частота видеопамяти: [0-9]*', sh_specs).group().removeprefix(
                'частота видеопамяти: ').split(' |', maxsplit=1)[0]
            print(info)
            return json.dumps(info), sh_specs
        case 'ssd':
            info['author'] = \
                re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                    0].split(' ')[0]
            info['ssd_drive_capacity'] = re.search('объем накопителя: [0-9]*', sh_specs).group().removeprefix(
                'объем накопителя: ')
            info['purpose'] = 'внутренний'
            info['type'] = 'ssd'
            info['form_factor'] = re.search('m.2|2.5"|pci-e aic', sh_specs).group()
            info['interface'] = \
                re.search('интерфейс: [\w\W]* [|]', sh_specs).group().removeprefix('интерфейс: ').split(' |',
                                                                                                        maxsplit=1)[
                    0]
            info['nvme_support'] = re.search('nvme: есть', sh_specs) is not None
            info['reading_speed'] = re.search('чтения: [0-9]*', sh_specs).group().removeprefix('чтения: ')
            info['writing_speed'] = re.search('записи: [0-9]*', sh_specs).group().removeprefix('записи: ')
            print(info)
            return json.dumps(info), full_info
        case 'hdd':
            info['author'] = re.search('seagate|toshiba|wd', full_name).group()
            info['hard_disk_capacity'] = re.search('[0-9]*.[0-9]* тб|[0-9]* тб|[0-9]* гб', sh_specs).group()
            info['purpose'] = 'внутренний'
            info['type'] = 'hdd'
            info['form_factor'] = '3.5"'
            info['interface'] = \
                re.search('интерфейс: [\w\W]* [|]', sh_specs).group().removeprefix('интерфейс: ').split(' |',
                                                                                                        maxsplit=1)[
                    0]
            info['rotational_speed'] = re.search('[0-9]* об/мин', sh_specs).group().removesuffix(' об/мин')
            print(info)
            return json.dumps(info), full_info
        case 'spu':
            info['author'] = \
                re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                    0].split(' ')[0]
            info['power'] = re.search('мощность: [0-9]*', sh_specs).group().removeprefix(
                'мощность ')
            info['form_factor'] = re.search(
                'sfx|tfx|atx', sh_specs).group()
            info['fan_size'] = re.search('размер вентилятора\(ов\): [0-9]*',
                                            sh_specs).group().removeprefix(
                'размер вентилятора(ов): ')
            certificate = re.search('сертифицирован в стандарте: [\w\W]* [|]', sh_specs)
            if certificate is not None:
                info['certificate'] = \
                    certificate.group().removeprefix('сертифицирован в стандарте: ').split(' |', maxsplit=1)[0]
            else:
                info['certificate'] = 'нет'
            print(info)
            return json.dumps(info), full_info
        case 'pc_case':
            info['author'] = \
            re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                0].split(' ')[0]
            info['form_factor'] = \
            re.search('форм-фактор: [\w\W]* [|]', sh_specs).group().removeprefix('форм-фактор: ').split(' |',
                                                                                                        maxsplit=1)[
                0]
            info['typesize'] = \
            re.search('типоразмер: [\w\W]* [|]', sh_specs).group().removeprefix('типоразмер: ').split(' |',
                                                                                                    maxsplit=1)[
                0]
            info['has_power_unit'] = re.search('мощность бп 0', sh_specs) is None
            info['is_window'] = re.search('боковая панель', sh_specs) is not None
            info['power_unit_position'] = \
            re.search('расположение бп: [\w\W]* [|]', sh_specs).group().removeprefix(
                'расположение бп: ').split(' |', maxsplit=1)[0]
            max_gpu_length = re.search('максимальная длина видеокарты: [0-9]*', sh_specs)
            if max_gpu_length is not None:
                info['max_gpu_length'] = max_gpu_length.group().removeprefix(
                    'максимальная длина видеокарты: ')
            else:
                info['max_gpu_length'] = 0
            max_cpu_height = re.search('максимальная высота кулера процессора: [0-9]*', sh_specs)
            if max_cpu_height is not None:
                info['max_cpu_height'] = max_cpu_height.group().removeprefix(
                    'максимальная высота кулера процессора: ')
            else:
                info['max_cpu_height'] = 0
            print(info)
            return json.dumps(info), full_info
        case 'cool_cpu':
            info['author'] = \
            re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                0].split(' ')[0]
            info['model'] = \
            re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |', maxsplit=1)[0]
            sockets = re.search('совместимость socket[\w\W]* да [|] т', sh_specs).group().replace(
                'совместимость ', '').replace(' да', '').replace(' | ', ', ').replace(':','').removesuffix(', т')
            info['socket'] = sockets
            info['fan_size'] = re.search('[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]* - [0-9]* об/мин|[0-9]* об/мин',
                                            sh_specs).group().removesuffix(
                ' об/мин')
            info['tdp'] = re.search('[0-9]* вт', sh_specs).group().removesuffix(' вт')
            print(info)
            return json.dumps(info), full_info
        case 'cool_lck':
            info['author'] = \
            re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                0].split(' ')[0]
            info['model'] = \
            re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |', maxsplit=1)[0]
            sockets = re.search('совместимость socket[\w\W]* да [|] т', sh_specs).group().replace(
                'совместимость ', '').replace(' да', '').replace(' | ', ', ').replace(':','').removesuffix(', т')
            info['socket'] = sockets
            info['type_cooling'] = 'СВО'
            info['fan_size'] = re.search('[0-9]* мм', sh_specs[0])
            info['fan_speed'] = re.search('[0-9]* - [0-9]* об/мин|[0-9]* об/мин', sh_specs[0]).group()
            info['tdp'] = re.search('[0-9]* вт', sh_specs[1]).group()
            print(info)
            return json.dumps(info), full_info
        case 'cool_case':
            info['author'] = \
            re.search('бренд: [\w\W]* [|]', sh_specs).group().removeprefix('бренд: ').split(' |', maxsplit=1)[
                0].split(' ')[0]
            info['model'] = \
            re.search('модель: [\w\W]* [|]', sh_specs).group().removeprefix('модель: ').split(' |', maxsplit=1)[0]
            info['fan_size'] = re.search('[0-9]* мм', sh_specs[0])
            info['fan_speed'] = re.search('[0-9]* - [0-9]* об/мин|[0-9]* об/мин', sh_specs[0]).group()
            print(info)
            return json.dumps(info), full_info