import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) 
sys.path.append(PROJECT_ROOT)

import json
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from description_parcer import params_description



def describer_regard(cat_name, driver):
    info = params_description.descriptor(cat_name).category
    full_info = dict()
    full_name = WebDriverWait(driver,15).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, 'h1.Product_title__42hYI'))).text.lower()
    params = driver.find_elements(By.CSS_SELECTOR, 'div.CharacteristicsItem_item__QnlK2')
    sh_specs = ''
    for spec in params:
        par_key = spec.find_element(By.CSS_SELECTOR, 'div.CharacteristicsItem_name__Q7B8V').find_element(By.CSS_SELECTOR, 'span').text.lower()
        par_val = spec.find_element(By.CSS_SELECTOR, 'div.CharacteristicsItem_value__fgPkc').text.lower()
        sh_specs = f'{sh_specs}{par_key}: {par_val} | '
        par_key = par_key
        full_info[par_key] = par_val
    sh_specs = sh_specs
    print(f'{sh_specs} \n\n {json.dumps(full_info)}')
    match cat_name:
        case 'cpu':
            if full_name.find('box (без кулера)') != -1:
                delivery_type = 'box (без кулера)'
            elif full_name.find('box') != -1:
                delivery_type = 'box'
            elif full_name.find('oem (с кулером)') != -1:
                delivery_type = 'oem (с кулером)'
            else:
                delivery_type = 'oem'
            info['author'] = re.search('intel|amd', sh_specs).group()
            info['line'] = re.search('линейка: [\w\W]{0,20} [|]', sh_specs).group().removeprefix('линейка: ').removesuffix(' |')
            info['model'] = re.search('модель: [\w\W]{0,10} [|]', sh_specs).group().removeprefix('модель: ').removesuffix(' |')
            info['socket'] = re.search('socket: [\w\W]{0,10} [|]', sh_specs).group().removeprefix('socket: ').removesuffix(' |')
            info['delivery_type'] = delivery_type
            info['core_number'] = re.search('количество ядер: [0-9]*', sh_specs).group().removeprefix(
                'количество ядер: ')
            info['threads_number'] = re.search('количество потоков: [0-9]*', sh_specs).group().removeprefix(
                'количество потоков: ')
            info['clock_frequency'] = re.search('тактовая частота: [0-9]*', sh_specs).group().removeprefix(
                'тактовая частота: ')
            boost_clock_frequency = re.search('в режиме turbo: [0-9]*', sh_specs)
            if boost_clock_frequency is None:
                info['boost_clock_frequency'] = 0
            else:
                info['boost_clock_frequency'] = boost_clock_frequency.group().removeprefix('в режиме turbo: ')
            info['core'] = \
                re.search('ядро: [\w\W]{0,15} [|]', sh_specs).group().removeprefix('ядро: ').removesuffix(' |')
            info['tdp'] = re.search('типичное тепловыделение: [0-9]*', sh_specs).group().removeprefix(
                'типичное тепловыделение: ')
            info['tech_process'] = re.search('технологический процесс: [0-9]*', sh_specs).group().removeprefix(
                'технологический процесс: ')
            integrated_video_core = re.search('интегрированное графическое ядро: да', sh_specs)
            if integrated_video_core is not None:
                info['integrated_video_core'] = \
                    re.search('видеопроцессор: [\w\W]{0,30} [|]', sh_specs).group().removeprefix(
                        'видеопроцессор: ').removesuffix(' |')
            else:
                info['integrated_video_core'] = 'нет'
            print(info)
            return json.dumps(info), full_info
        case 'mb':
            print(sh_specs)
            info['author'] = full_name.removeprefix('материнская плата ').split(' |', maxsplit=1)[0]
            chipset = re.search('amd [\w\W][0-9]{3}|amd [\w\W][0-9]{3}e|amd wrx80|intel [\w\W][0-9]*', sh_specs)
            info['chipset'] = chipset.group()
            socket = re.search('am[0-9]|swrx8|lga [0-9]*', sh_specs)
            info['socket'] = socket.group()
            info['memory_type'] = \
                re.search('тип памяти: [\w\W]* [|]', sh_specs).group().removeprefix('тип памяти: ').split(' |',
                                                                                                        maxsplit=1)[
                    0]
            info['memory_type_amount'] = re.search('количество слотов памяти: [0-9]*',
                                                    sh_specs).group().removeprefix('количество слотов памяти: ')
            form_factor = re.search('atx|matx|e-atx|eatx|mini-itx|thin mini-itx|mini-dtx|ssi ceb|microatx',
                                    sh_specs)
            info['form_factor'] = form_factor.group()
            m2_amount = re.findall('m key', sh_specs)
            info['m2_amount'] = len(m2_amount)
            print(full_name, info)
            return json.dumps(info), full_info
        case 'ram':
            author = re.search(
                'kingston|amd|patriot memory|netac|g.skill|acer|adata|afox|agi|apacer|biwintech|cbr|corsair|crucial|digma|exegate|foxline|geil|gigabyte|hikvision|hp|hynix|infortrend|kimtigo|kingmax|kingspec|klevv|patriot|ocpc|qnap|qumo|samsung|silicon power|team|transcend|тми',
                full_name)
            info['author'] = author.group()
            memory_amount = re.search('[0-9]*gb', full_name)
            if memory_amount is not None:
                info['memory_amount'] = memory_amount.group().removesuffix('gb')
            else:
                memory_amount = re.search('[0-9]* гб', sh_specs)
                if memory_amount is not None:
                    info['memory_amount'] = memory_amount.group().split(' гб')[0]
                else:
                    info['memory_amount'] = ''
            memory_type = re.search('ddr[0-9]', sh_specs)
            if memory_type is not None:
                info['memory_type'] = memory_type.group()
            else:
                info['memory_type'] = ''
            memory_frequency = re.search('[0-9]*mhz', full_name)
            if memory_frequency is not None:
                info['memory_frequency'] = memory_frequency.group().split('mhz')[0]
            else:
                info['memory_frequency'] = ''
            is_kit = re.search('количество модулей в комплекте: [0-9]', full_name)
            info['is_kit'] = 0 if is_kit is None else int(is_kit.group().removeprefix(
                'количество модулей в комплекте: '))
            memory_speed = re.search('[0-9]* мб/с', sh_specs)
            if memory_speed is not None:
                info['memory_speed'] = memory_speed.group().split(' мб/с')[0]
            else:
                info['memory_speed'] = ''
            info['latency'] = re.search('\(cl\): [0-9]*', sh_specs).group().removeprefix('(cl): ')
            is_XMP = re.search('xmp', sh_specs)
            info['is_XMP'] = False if is_XMP is None else True
            print(info)
            return json.dumps(info), full_info
        case 'gpu':
            author = re.search(
                '(asrock|asus|biostar|colorful|gainward|gigabyte|inno3d|kfa2|maxsun|msi|palit|pny|powercolor|sapphire|zotac)',
                full_name)
            if author is not None:
                info['video_card_author'] = author.group()
            else:
                author = re.search('nvidia|amd', full_name)
                info['video_card_author'] = author.group()
            print(sh_specs)
            try:
                cpu_author = re.search('nvidia|amd|intel', full_name)
                info['author'] = cpu_author.group()
                memory_amount = re.search('[0-9]*gb', full_name)
                info['model'] = full_name.split(cpu_author.group())[1].split(author.group())[0].strip()
                info['memory_amount'] = memory_amount.group().removesuffix('gb')
                info['interface'] = re.search('pci express [0-9]*.0', sh_specs).group()
                info['clock_frequency'] = re.search('частота графического процессора: [0-9]*',
                                                    sh_specs).group().removeprefix(
                    'частота графического процессора: ')
                memory_type = re.search('ddr[0-9]|gddr[0-9]x|gddr[0-9]|hbm2', sh_specs).group()
                info['memory_type'] = memory_type
                info['memory_frequency'] = re.search(f'частота видеопамяти: [0-9]*',
                                                        sh_specs).group().rsplit(' ',maxsplit=1)[1]
                print(info)
            except AttributeError:
                print(full_name, info, 'NO DATA')
                raise ValueError
            return json.dumps(info), full_info
        case 'ssd':
            info['author'] = full_name.split(' ')[3]
            info['ssd_drive_capacity'] = full_name.split(' ')[2]
            info['purpose'] = 'внутренний'
            info['type'] = 'ssd'
            info['form_factor'] = re.search('m.2|2.5"|pci-e aic', sh_specs).group()
            info['interface'] = re.search('msata|sata-iii|ide|u.2|usb 3.0|pci-e xp[0-9]|pci-e [45].0 x4|pci-e',
                                            sh_specs).group()
            info['nvme_support'] = re.search('nvme', sh_specs) is not None
            info['reading_speed'] = re.search('чтения: [0-9]*', sh_specs).group().removeprefix('чтения: ')
            info['writing_speed'] = re.search('записи: [0-9]*', sh_specs).group().removeprefix('записи: ')
            return json.dumps(info), full_info
        case 'hdd':
            info['author'] = re.search('seagate|toshiba|wd', full_name).group()
            info['hard_disk_capacity'] = full_name.split(' ')[2]
            info['interface'] = re.search('sata-iii|sata-ii', sh_specs).group()
            info['purpose'] = 'внутренний'
            info['type'] = 'hdd'
            info['form_factor'] = re.search('3.5"|2.5"', sh_specs).group()
            rotational_speed = re.search('[0-9]* об/мин', sh_specs)
            if rotational_speed is not None:
                info['rotational_speed'] = re.search('[0-9]* об/мин', sh_specs).group().removesuffix(' об/мин')
            else:
                info['rotational_speed'] = 'NULL'
            return json.dumps(info), full_info
        case 'spu':
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
            info['author'] = full_name.split(' ')[1]
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
            info['author'] = full_name.removeprefix('кулер ').split(' ')[0]
            info['model'] = full_name.removeprefix('кулер ').split(' ', maxsplit=1)[1]
            info['socket'] = \
                re.search('socket: [\w\W]* \|', sh_specs).group().removeprefix('socket: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['fan_size'] = re.search('[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            info['tdp'] = re.search('[0-9]* вт', sh_specs).group().removesuffix(' вт')
            print(info)
            return json.dumps(info), full_info
        case 'cool_lck':
            info['author'] = full_name.removeprefix('система жидкостного охлаждения ').split(' ')[0]
            info['model'] = full_name.removeprefix('система жидкостного охлаждения ').split(' ', maxsplit=1)[1]
            info['type_cooling'] = 'сво'
            info['socket'] = \
                re.search('socket: [\w\W]* [|]', sh_specs).group().removeprefix('socket: ').split(' |',
                                                                                                maxsplit=1)[0]
            info['fan_size'] = re.search('[0-9]*x[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            return json.dumps(info), full_info
        case 'cool_case':
            info['author'] = full_name.removeprefix('вентиляторы ').removeprefix('вентилятор ').removeprefix('для корпуса ').split(' ')[0]
            info['model'] = full_name.removeprefix('вентиляторы ').removeprefix('вентилятор ').removeprefix('для корпуса ').split(' ', maxsplit=1)[1]
            info['fan_size'] = re.search('[0-9]* мм', sh_specs).group().removesuffix(' мм')
            info['fan_speed'] = re.search('[0-9]*-[0-9]* об/мин|[0-9]* об/мин', sh_specs).group().removesuffix(
                ' об/мин')
            return json.dumps(info), full_info