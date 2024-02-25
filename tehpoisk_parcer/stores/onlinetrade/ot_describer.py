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
from selenium.common.exceptions import TimeoutException
from description_parcer import params_description

def describer_ot(cat_name, driver):
    info = params_description.descriptor().category
    full_info = dict()
    try:
            WebDriverWait(driver, 15).until(
                expected_conditions.element_to_be_clickable((By.ID, 'ui-id-2'))).click()
    except TimeoutException:
        try:
            driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/div[3]/form/div/div/input[3]').click()
            WebDriverWait(driver, 15).until(
                    expected_conditions.element_to_be_clickable((By.ID, 'ui-id-2'))).click()
        except TimeoutException:
            raise AttributeError
    full_name = driver.find_element(By.CSS_SELECTOR, 'h1').text.lower()
    params = driver.find_element(By.CSS_SELECTOR,'ul.featureList.js__backlightingClick').find_elements(By.CSS_SELECTOR, 'li.featureList__item')
    sh_specs = ''
    for spec in params:
        spec_key = spec.find_element(By.CSS_SELECTOR,'span').text.lower()
        spec_val = spec.text.lower().removeprefix(spec_key)
        sh_specs = f'{sh_specs}{spec_key} {spec_val} | '
        full_info[spec_key] = spec_val
    sh_specs = sh_specs.removeprefix(' | ').lower().replace('\n', ' ')
    print(sh_specs)    
    match cat_name: 
        case 'cpu':
            part_name = full_name.split(' box')[0].split(' oem')[0].split(' оем')[0]
            part_name = part_name.rsplit(' ', maxsplit=1)[0]
            part_name = part_name.replace('-', ' ')
            line = ''
            if part_name.find('intel') != -1:
                info['author'] = 'intel'
                lines = list(['core i5', 'core i3', 'core i7', 'core i9', 'pentium', 'pentium', 'celeron'])
            else:
                info['author'] = 'amd'
                lines = list(
                    ['sempron', 'athlon', 'athlon x2', 'a6', 'fx', 'a8', 'a12', 'epyc', 'ryzen threadripper', 'ryzen 3',
                    'ryzen 5', 'ryzen 7', 'ryzen 9'])
            for line_name in lines:
                if part_name.find(line_name) != -1:
                    line = line_name
                    if line_name == 'athlon' and part_name.find('pro') != -1:
                        line = 'pro athlon'
                    if part_name.find('ryzen') != -1 and part_name.find('pro') != -1:
                        line = f'{line_name} pro'
                    # info['line'] = line
                    break
            if line == 'pentium':
                part_name = str(part_name).replace(' gold', '')
            if part_name.find('threadripper') != -1 and part_name.find('pro') == -1:
                part_name = part_name.replace('threadripper', 'threadripper pro')
            model = part_name.split(line)[1].strip()
            info['model'] = model
            info['delivery_type'] = re.search('тип поставки: [\w\W]* [|]', sh_specs).group().removeprefix('тип поставки: ').split(' |',maxsplit=1)[0]
            info['socket'] = re.search('тип разъема \(socket\): [\w\W]* [|]', sh_specs).group().removeprefix('тип разъема (socket): ').split(' |',maxsplit=1)[0]
            info['core_number'] = re.search('[0-9]* яд[ра|ер]', sh_specs).group().split(' ')[0]
            info['core'] = re.search('ядро: [\w\W]* [|]', sh_specs).group().removeprefix('ядро: ').split(' |',maxsplit=1)[0]
            info['clock_frequency'] = re.search('номинальная частота \(ггц\): [0-9]*.[0-9]*', sh_specs).group().rsplit(' ',maxsplit=1)[1]
            boost_clock_frequency = re.search('частота в турбо режиме \(ггц\): [0-9]*.[0-9]*', sh_specs)
            info['boost_clock_frequency'] = boost_clock_frequency.group().rsplit(' ',maxsplit=1)[1] if boost_clock_frequency is not None else 0 
            info['threads_number'] = info['core_number'] = re.search('[0-9]* поток[а|ов]', sh_specs).group().split(' ')[0]
            info['tdp'] = re.search('[0-9]* вт',sh_specs).group()
            tech_process = re.search('[0-9]* нм',sh_specs)
            if tech_process is not None:
                info['tech_process'] = re.search('[0-9]* нм',sh_specs).group()
            else:
                info['tech_process'] = '0'
            ivc = re.search('[intel [uhd|hd] graphics [0-9]*|radeon [r[0-9]*]|ve]', sh_specs)
            info['integrated_video_core'] = ivc.group() if ivc is not None else 'нет'
            # image_urls = page.find_element(By.CSS_SELECTOR, 'img').get_attribute('src')
            return json.dumps(info), full_info
        case 'mb':
            part_name = full_name.split(' (', maxsplit=1)[0]
            info['author'] = full_name.removeprefix("материнская плата ").split(' ')[0]
            chipset = re.search('amd [\w\W][0-9]{3}|amd [\w\W][0-9]{3}e|amd wrx80|intel [\w\W][0-9]*', sh_specs)
            info['chipset'] = chipset.group()
            socket = re.search('am[0-9]|swrx8|lga [0-9]*', sh_specs)
            info['socket'] = socket.group()
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_type_amount = re.search('кол-во слотов памяти: [0-9]*', sh_specs).group().removeprefix(
                'количество слотов памяти: ')
            info['memory_type_amount'] = int(memory_type_amount)
            form_factor = re.search('atx|matx|e-atx|mini-itx|thin mini-itx|mini-dtx|ceb|microatx', full_name)
            info['form_factor'] = form_factor.group()
            m2_amount = re.search('кол-во слотов m.2: нет', sh_specs)
            if m2_amount is None:
                info['m2_amount'] = re.search('кол-во слотов m.2: [0-9]*', sh_specs).group().removeprefix(
                    'кол-во слотов m.2: ')
            else:
                info['m2_amount'] = 0
            # потенциально нерабочее решение по поиску м2, перепроверить
            
            return json.dumps(info), full_info
        case 'ram':
            if re.search('уценка', full_name) is not None:
                raise ValueError
            author = re.search('kingston|amd|patriot memory|netac|g.skill|acer|adata|afox|agi|apacer|biwintech|cbr|corsair|crucial|digma|exegate|foxline|geil|gigabyte|hikvision|hp|hyxis|infortrend|kimtigo|kingmax|kingspec|ocpc|qnap|qumo|samsung|silicon power|team group|terramaster|thermaltake|transcend|тми', full_name)
            info['author'] = author.group()
            memory_amount = re.search('[0-9]*gb', full_name)
            info['memory_amount'] = memory_amount.group().removesuffix('gb')
            memory_type = re.search('ddr[0-9]', sh_specs)
            info['memory_type'] = memory_type.group()
            memory_frequency = re.search('[0-9]* мгц', sh_specs)
            info['memory_frequency'] = memory_frequency.group().split(' мгц')[0]
            is_kit = re.search('кол-во модулей в упаковке: [0-9]', sh_specs)
            info['is_kit'] = 0 if is_kit is None else int(is_kit.group().removeprefix(
                'кол-во модулей в упаковке: '))
            memory_speed = re.search('[0-9]* мб/с', sh_specs)
            if memory_speed is not None:
                info['memory_speed'] = memory_speed.group().split(' мб/с')[0]
            else:
                info['memory_speed'] = ''
            info['latency'] = re.search('cl[0-9]*', sh_specs).group().removeprefix('cl')
            is_XMP = re.search('xmp', sh_specs)
            info['is_XMP'] = False if is_XMP is None else True
            return json.dumps(info), full_info
        case 'gpu':
            if re.search('уценка', full_name) is not None:
                raise ValueError
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
        case 'ssd':
            info['author'] = full_name.split(' ')[2]
            info['ssd_drive_capacity'] = full_name.split(' ')[1]
            info['purpose'] = 'внутренний'
            info['type'] = 'ssd'
            info['form_factor'] = re.search('m.2|2.5"|pci-e aic', sh_specs).group()
            info['interface'] = re.search('msata|sata-iii|ide|u.2|usb 3.0|pci-e xp[0-9]|pci-e [45].0 x4|pci-e',
                                            sh_specs).group()
            info['nvme_support'] = re.search('nvme', sh_specs) is not None
            info['reading_speed'] = re.search('чтения до: [0-9]*', sh_specs).group().removeprefix('чтения до: ')
            info['writing_speed'] = re.search('записи до: [0-9]*', sh_specs).group().removeprefix('записи до: ')
            return json.dumps(info), sh_specs
        case 'hdd':
            info['author'] = re.search('seagate|toshiba|wd', full_name).group()
            info['hard_disk_capacity'] = full_name.split(' ')[3]
            info['interface'] = re.search('sata iii|sata ii', sh_specs).group()
            info['purpose'] = 'внутренний'
            info['type'] = 'hdd'
            info['form_factor'] = re.search('3.5 "|2.5 "', sh_specs).group()
            info['rotational_speed'] = re.search('[0-9]* об/мин', sh_specs).group().removesuffix(' об/мин')
            return json.dumps(info), sh_specs
        case 'spu':
            if re.search('уценка', full_name) is not None:
                raise ValueError
            info['author'] = \
                re.search('производитель: [\w\W]* [|]', sh_specs).group().removeprefix('производитель: ').split(
                    ' |',
                    maxsplit=1)[
                    0]
            info['power'] = full_name.removeprefix('блок питания ').split(' ', maxsplit=1)[0]
            info['form_factor'] = re.search(
                'atx12v [0-9].[0-9]*|atx12v|flex atx|sfx-l|sfx12v [0-9].[0-9]*|sfx12v|tfx12v [0-9].[0-9]*|tfx12v',
                sh_specs).group()
            info['fan_size'] = re.search('размер вентилятора: [0-9]*', sh_specs).group().removeprefix(
                'размер вентилятора: ')
            certificate = re.search('сертификат 80 plus: [\w\W]* [|]', sh_specs)
            if certificate is not None:
                info['certificate'] = \
                    certificate.group().removeprefix('сертификат 80 plus: ').split(' |', maxsplit=1)[0]
            else:
                info['certificate'] = 'нет'
            print(info)
            return json.dumps(info), full_info
        case 'pc_case':
            info['author'] = full_name.split(' ')[0]
            info['form_factor'] = re.search(
                'full-desktop|full-tower|micro-tower|midi-tower|mini-tower|slim-desktop|super-tower',
                sh_specs).group()
            info['typesize'] = ','.join(re.findall(
                'atx|e-atx|ee-atx|flexatx|matx|mbtx|mini-dtx|mini-itx|mini-stx|ssi ceb|ssi eeb|thin mini-itx|xl-atx',
                sh_specs))
            info['has_power_unit'] = re.search('без бп', sh_specs) is None
            info['is_window'] = re.search('наличие окна', sh_specs) is not None
            info['power_unit_position'] = \
                re.search('расположение бп: [\w\W]* [|]', sh_specs).group().removeprefix(
                    'расположение бп: ').split(
                    ' |', maxsplit=1)[0]
            max_gpu_length = re.search('максимальная длина видеокарты: [0-9]*', sh_specs)
            if max_gpu_length is not None:
                info['max_gpu_length'] = max_gpu_length.group().removeprefix('максимальная длина видеокарты: ')
            else:
                info['max_gpu_length'] = 0
            max_cpu_height = re.search('максимальная высота кулера: [0-9]*', sh_specs)
            if max_cpu_height is not None:
                info['max_cpu_height'] = max_cpu_height.group().removeprefix('максимальная высота кулера: ')
            else:
                info['max_cpu_height'] = 0
            print(info)
            return json.dumps(info), full_info
        case 'cool_cpu':
            info['author'] = full_name.removeprefix('кулер для процессора ').split(' ')[0]
            info['model'] = full_name.removeprefix('кулер для процессора ').split(' ', maxsplit=1)[1]
            info['socket'] = re.search('socket: [\w\W]* \|', sh_specs).group().removeprefix('socket: ').split(' |',maxsplit=1)[0]
            info['fan_size'] = re.search('[0-9]*x[0-9]*x[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            info['tdp'] = re.search('[0-9]* вт', sh_specs).group().removesuffix(' вт')
            print(info)
            return json.dumps(info), full_info
        case 'cool_lck':
            info['author'] = full_name.removeprefix('сво для процессора ').split(' ')[0]
            info['model'] = full_name.removeprefix('сво для процессора ').split(' ', maxsplit=1)[1]
            info['type_cooling'] = 'сво'
            info['socket'] = \
                re.search('socket [\w\W]* [|]', sh_specs).group().removeprefix('socket ').split(' |',
                                                                                                maxsplit=1)[0]
            info['fan_size'] = re.search('[0-9]*x[0-9]*x[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            return json.dumps(info), full_info
        case 'cool_case':
            info['author'] = full_name.removeprefix('вентиляторы ').removeprefix('вентилятор ').removeprefix('для корпуса ').split(' ')[0]
            info['model'] = full_name.removeprefix('вентиляторы ').removeprefix('вентилятор ').removeprefix('для корпуса ').split(' ', maxsplit=1)[1]
            info['fan_size'] = re.search('[0-9]*x[0-9]*x[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            return json.dumps(info), full_info