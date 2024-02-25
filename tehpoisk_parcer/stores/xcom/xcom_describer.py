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

def describer_xcom(cat_name, driver):
    info = params_description.descriptor().category
    full_info = dict()
    try:
        full_name = WebDriverWait(driver,5).until(expected_conditions.presence_of_element_located((By.ID, 'card-main-title'))).text.lower()
        specifications = WebDriverWait(driver,5).until(expected_conditions.presence_of_element_located((By.ID, 'specifications')))
        params = WebDriverWait(specifications,5).until(expected_conditions.presence_of_all_elements_located((By.CSS_SELECTOR,'li.product-block-description__item')))
    except:
        return 'INVALID', 'INVALID'
    sh_specs = ''
    time.sleep(0.5)
    driver.find_element(By.CSS_SELECTOR, 'button.product-block-description__btn').click()
    for spec in params:
        spec_key = spec.find_element(By.CSS_SELECTOR,'div.product-block-description__first-elem').text.lower()
        spec_val = spec.find_element(By.CSS_SELECTOR,'div.product-block-description__second-elem').text.lower()
        print(f'{spec_key}: {spec_val}')
        sh_specs = f"{sh_specs}{spec_key}: {spec_val} | "
        full_info[spec_key] = spec_val
    sh_specs = sh_specs.lower()
    print(sh_specs)
    match cat_name:
        case 'cpu':
            line = ''
            intel_line = re.search('intel i[0-9]', full_name)
            if intel_line is not None:
                full_name = full_name.replace('intel', 'intel core')
            amd_line = re.search('amd threadripper', full_name)
            if amd_line is not None:
                full_name = full_name.replace('amd threadripper', 'amd ryzen threadripper')
            if full_name.find('intel') != -1:
                info['author'] = 'intel'
                full_name = full_name.replace('-', ' ')
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'pentium', 'celeron'])
                sockets = list(
                    ['lga1151', 'lga1151 for gen8', 'lga1151v2', 'lga1200', 'lga1700', 'lga2011-v3', 'lga2066'])
            else:
                info['author'] = 'amd'
                lines = list(
                    ['athlon', 'a6', 'a8', 'a12', 'epyc', 'ryzen threadripper', 'ryzen 3',
                        'ryzen 5', 'ryzen 7', 'ryzen 9'])
                sockets = list(['am4', 'am5', 'swrx8'])
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
                    info['socket'] = socket
                    if socket == 'lga1151 for gen8' or (socket == 'lga1151' and (
                            full_name == 'intel core i3-9100t' or full_name == 'intel core i5-9400f')):
                        info['socket'] = 'lga1151v2'
            if line == 'pentium':
                full_name = str(full_name).replace(' gold', '')
            if line == 'ryzen 5':
                full_name = full_name.replace(' oem', '')
            if line == '':
                print(full_name)
                print('SOMETHING WRONG WITH THE NAME')
            info['model'] = \
                re.search('модельный ряд: [\w\W]* [|]', sh_specs).group().removeprefix('модельный ряд: ').split(
                    ' |',
                    maxsplit=1)[
                    0]
            info['delivery_type'] = \
                re.search('вид поставки: [\w\W]* [|]', sh_specs).group().removeprefix('вид поставки: ').split(
                    ' |',
                    maxsplit=1)[
                    0]
            info['clock_frequency'] = int(float(
                re.search('частота процессора: [0-9]*.[0-9]*|частота процессора: [0-9]*',
                            sh_specs).group().removeprefix('частота процессора: ')) * 1000)
            boost_clock_frequency = re.search('в турбо режиме: [0-9]*.[0-9]*|в турбо режиме: [0-9]*',
                                                sh_specs).group().removeprefix('в турбо режиме: ')
            if boost_clock_frequency is not None:
                info['boost_clock_frequency'] = int(float(boost_clock_frequency) * 1000)
            wattson = re.search('[0-9]*w|[0-9]*  вт', sh_specs)
            if wattson is not None:
                tdp = wattson.group().removesuffix('w').removesuffix(' вт')
                info['tdp'] = tdp.strip()
            techprocess = re.search('[0-9]*  нм|[0-9]*nm', sh_specs)
            if techprocess is not None:
                tech_process = techprocess.group().removesuffix('nm').removesuffix(' нм')
                info['tech_process'] = tech_process.strip()
            info['core_number'] = re.search('количество ядер: [0-9]*', sh_specs).group().removeprefix(
                'количество ядер: ')
            info['threads_number'] = re.search('количество потоков: [0-9]*', sh_specs).group().removeprefix(
                'количество потоков: ')
            int_vd_core = re.search('интегрированное графическое ядро: нет', sh_specs)
            if int_vd_core is not None:
                info['integrated_video_core'] = \
                    re.search('модель графического процессора: [\w\W]* [|]', sh_specs).group().removeprefix(
                        'модель графического процессора: ').split(' |', maxsplit=1)[0]
            else:
                info['integrated_video_core'] = 'нет'
            print(info)
            
            
        case 'mb':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['chipset'] = \
                re.search('чипсет: [\w\W]* [|]', sh_specs).group().removeprefix('чипсет: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['socket'] = \
                re.search('сокет: [\w\W]* [|]', sh_specs).group().removeprefix('сокет: ').split(' |', maxsplit=1)[
                    0]
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_type_amount = re.search('количество слотов памяти: [0-9]*', sh_specs).group().removeprefix(
                'количество слотов памяти: ')
            info['memory_type_amount'] = int(memory_type_amount)
            info['form_factor'] = re.search(
                'atx|matx|e-atx|eatx|mini-itx|thin mini-itx|mini-dtx|ssi ceb|microatx', sh_specs).group()
            m2_amount = re.search('m.2 \(socket 3\) [0-9]*', sh_specs)
            if m2_amount is not None:
                info['m2_amount'] = int(
                    re.search('m.2 \(socket 3\) [0-9]*', sh_specs).group().removeprefix('m.2 (socket 3) '))
            else:
                info['m2_amount'] = 0
            print(full_name, info)
            
        case 'ram':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            memory_amount = re.search('[0-9]*gb', full_name)
            info['memory_amount'] = memory_amount.group().removesuffix('gb')
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_frequency = re.search('[0-9]*  мгц', sh_specs)
            if memory_frequency is not None:
                info['memory_frequency'] = memory_frequency.group().split('mhz')[0]
            else:
                info['memory_frequency'] = ''
            is_kit = re.search('количество модулей в комплекте: 1', sh_specs)
            info['is_kit'] = 'нет' if is_kit is not None else is_kit.group().removeprefix(
                'количество модулей в комплекте: ')
            info['memory_speed'] = re.search('[0-9]*  мб/c', sh_specs).group().removesuffix('  мб/c')
            latency = re.search('\(cl\): [0-9]*', sh_specs)
            info['latency'] = latency.group().removeprefix('(cl): ')
            info['is_XMP'] = re.search('xmp совместимая память: да', sh_specs) is not None
            print(info)
            
        case 'gpu':
            info['author'] = re.search('intel|amd|nvidia', sh_specs).group()
            h2 = driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower()
            info['model'] = h2.split(' ', maxsplit=2)[2].split('(')[0]
            info['video_card_author'] = h2.split(' ')[1]
            memory_amount = re.search('видеопамяти: [0-9]*', sh_specs)
            info['memory_amount'] = memory_amount.group().removeprefix('видеопамяти: ')
            interface = re.search('pci-e x[0-9]*', sh_specs).group() + f" {re.search('версия интерфейса: [0-9]*', sh_specs).group().removeprefix('версия интерфейса: ')}"
            info['interface'] = interface
            info['clock_frequency'] = re.search('частота: [0-9]*', sh_specs).group().removeprefix('частота: ')
            info['memory_frequency'] = re.search('частота памяти: [0-9]*', sh_specs).group().removeprefix(
                'частота памяти: ')
            info['memory_type'] = re.search('ddr[0-9]|gddr[0-9]x|gddr[0-9]|hbm2', sh_specs).group()
            print(info)
            
        case 'ssd':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['ssd_drive_capacity'] = re.search('[0-9]*.[0-9]*  tb|[0-9]*  tb|[0-9]*  gb', sh_specs).group()
            info['purpose'] = 'внутренний'
            info['type'] = 'ssd'
            form_factor = re.search('m.2 [0-9]*|m.2|2.5"|pci-e|pcie|u.2|msata', sh_specs)
            if form_factor is not None:
                info['form_factor'] = re.search('m.2 [0-9]*|m.2|2.5"|pci-e|pcie', sh_specs).group()
            else:
                info['form_factor'] = ''
            info['interface'] = re.search(
                'msata|sata-iii|ide|u.2|usb 3.0|pci-e xp[0-9]|pci-e [0-9].[0-9] x4|pci-e gen[0-8] x[0-9]|pci-e gen4|pci-e',
                sh_specs).group()
            revision = re.search('ревизия pci-e: [0-9]*[0-9]*', sh_specs)
            if revision is not None:
                info['interface'] = f'pci-e {revision.group().removeprefix("ревизия pci-e: ")}'
            info['nvme_support'] = re.search('поддержка nvme: есть', sh_specs) is not None
            info['reading_speed'] = re.search('чтения: [0-9]*', sh_specs).group().removeprefix('чтения: ')
            info['writing_speed'] = re.search('записи: [0-9]*', sh_specs).group().removeprefix('записи: ')
            print(info)
            
        case 'hdd':
            info['author'] = re.search('seagate|toshiba|western digital', full_name).group()
            info['hard_disk_capacity'] = re.search('[0-9]*.[0-9]*  tb|[0-9]*  tb|[0-9]*  гб', sh_specs).group()
            info['purpose'] = 'внутренний'
            info['type'] = 'hdd'
            info['form_factor'] = re.search('3.5"|2.5"', sh_specs).group()
            info['interface'] = re.search('sata|sas', sh_specs).group()
            info['rotational_speed'] = re.search('[0-9]*  об/мин', sh_specs).group().removesuffix('об/мин')
            print(info)
            
        case 'spu':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['power'] = re.search('номинальная мощность: [0-9]*', sh_specs).group().removeprefix(
                'номинальная мощность: ')
            info['form_factor'] = re.search(
                'flex atx|eps|ps/2|sfx|tfx|atx', sh_specs).group()
            info['fan_size'] = re.search('диаметр установленных вентиляторов: [0-9]*',
                                            sh_specs).group().removeprefix(
                'диаметр установленных вентиляторов: ')
            certificate = re.search('сертификат 80 plus: [\w\W]* [|]', sh_specs)
            info['certificate'] = \
                certificate.group().removeprefix('сертификат 80 plus: ').split(' |', maxsplit=1)[0]
            print(info)
            
        case 'pc_case':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            typesize = re.search(
                'нестандартный|super tower|small form factor|slim desktop|rackmount|nettop|mini tower|midi tower|micro tower|full tower|desktop mini|desktop',
                sh_specs)
            info['typesize'] = typesize.group() if typesize is not None else ''
            info['form_factor'] = ','.join(re.findall(
                'atx|ee-atx|e-atx|flexatx|matx|mbtx|mini-dtx|mini-itx|mini-stx|ssi ceb|ssi eeb|thin mini-itx|xl-at',
                sh_specs))
            info['has_power_unit'] = re.search('наличие блока питания: есть', sh_specs) is not None
            info['is_window'] = re.search('стекло|окно', sh_specs) is not None
            info['power_unit_position'] = \
                re.search('расположение блока питания: [\w\W]* [|]', sh_specs).group().removeprefix(
                    'расположение блока питания: ').split(' |', maxsplit=1)[0]
            info['max_gpu_length'] = re.search('длина карт расширения: [0-9]*', sh_specs).group().removeprefix(
                'длина карт расширения: ')
            info['max_cpu_height'] = re.search('высота кулера CPU: [0-9]*', sh_specs).group().removeprefix(
                'высота кулера CPU: ')
            print(info)
            
        case 'cool_cpu':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['model'] = full_name.split(' ', maxsplit=1)[1]
            sockets = \
                re.search('сокет [\w\W]* [|]', sh_specs).group().removeprefix('сокет ').split(' |', maxsplit=1)[
                    0]
            info['socket'] = sockets
            info['fan_size'] = \
                re.search('диаметр вентилятора [0-9]*|диаметр вентиляторов [0-9]*', sh_specs).group().rsplit(
                    ' ',
                    maxsplit=1)[
                    1]
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            tdp = re.search('[0-9]*  вт', sh_specs)
            info['tdp'] = tdp.group()
            print(info)
            
        case 'cool_lck':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['model'] = full_name.split(' ', maxsplit=1)[1]
            info['type_cooling'] = 'сво'
            sockets = \
                re.search('сокет [\w\W]* [|]', sh_specs).group().removeprefix('сокет ').split(' |', maxsplit=1)[
                    0]
            info['socket'] = sockets
            info['fan_size'] = \
                re.search('диаметр вентилятора [0-9]*|диаметр вентиляторов [0-9]*', sh_specs).group().rsplit(
                    ' ',
                    maxsplit=1)[
                    1]
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            print(info)
            
        case 'cool_case':
            info['author'] = \
                driver.find_element(By.CSS_SELECTOR,
                                    'h2.product-block-description__title.mb40').text.lower().split(
                    ' ')[1]
            info['model'] = full_name.split(' ', maxsplit=1)[1]
            info['fan_size'] = \
                re.search('диаметр вентилятора: [0-9]*|диаметр вентиляторов: [0-9]*', sh_specs).group().rsplit(
                    ' ',
                    maxsplit=1)[
                    1]
            fan_max = re.search('максимальная скорость вращения: [0-9]*', sh_specs)
            fan_min = re.search('минимальная скорость вращения: [0-9]*', sh_specs)
            if fan_min is not None:
                fan_speed = f"{fan_max.group().removeprefix('максимальная скорость вращения: ')}-{fan_min.group().removeprefix('минимальная скорость вращения: ')}"
            else:
                fan_speed = fan_max.group().removeprefix('максимальная скорость вращения: ')
            info['fan_speed'] = fan_speed
            print(info)
    return json.dumps(info), full_info
    