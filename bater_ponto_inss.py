from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import UnexpectedAlertPresentException, TimeoutException
import time
import re

SIAPE = ""     # Seu SIAPE
SENHA = ""    # Sua senha
URL_LOGIN = "https://sisref.inss.gov.br/entrada.php"
TEMPO_ESPERA_CAPTCHA = 10  # segundos para você preencher o CAPTCHA manualmente

def tempo_trabalhado_em_minutos(texto):
    match = re.search(r"(\d+)\s*horas.*?(\d+)\s*minutos", texto)
    if match:
        horas = int(match.group(1))
        minutos = int(match.group(2))
        return horas * 60 + minutos
    return 0

def tentar_login():
    while True:
        driver = webdriver.Chrome()
        driver.get(URL_LOGIN)
        try:
            campo_siape = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.ID, "lSiape"))
            )
            campo_siape.send_keys(SIAPE)

            campo_senha = driver.find_element(By.ID, "lSenha")
            campo_senha.send_keys(SENHA)

            print(f"⏳ Preencha o CAPTCHA manualmente em até {TEMPO_ESPERA_CAPTCHA} segundos...")
            time.sleep(TEMPO_ESPERA_CAPTCHA)

            botao_entrar = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@id='btn-enviar']"))
            )
            botao_entrar.click()

            # Espera a URL mudar, sinalizando login bem-sucedido
            WebDriverWait(driver, 10).until(EC.url_changes(URL_LOGIN))

            print("✅ Login realizado com sucesso!")
            return driver

        except UnexpectedAlertPresentException as alerta:
            print("⚠️ CAPTCHA não informado ou incorreto! Reiniciando login...")
            try:
                alert = driver.switch_to.alert
                print(f"🟨 Alerta: {alert.text}")
                alert.accept()
            except Exception:
                pass
            driver.quit()

        except TimeoutException:
            print("❌ Tempo esgotado durante login ou elementos não encontrados. Tentando novamente...")
            driver.quit()

        except Exception as e:
            print(f"❌ Erro inesperado no login: {e}")
            driver.quit()
            break

def verificar_tempo_trabalhado(driver):
    try:
        while True:
            tempo_elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'horas') and contains(text(),'minutos')]"))
            )
            texto_tempo = tempo_elemento.text
            minutos_trabalhados = tempo_trabalhado_em_minutos(texto_tempo)
            minutos_faltando = 360 - minutos_trabalhados  # 6 horas = 360 minutos

            print(f"⏱ Tempo atual: {texto_tempo} → {minutos_trabalhados} minutos trabalhados")

            if minutos_trabalhados >= 360:
                print("✅ Já trabalhou 6 horas ou mais! Fechando o ponto...")

                botao_encerrar = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//img[@alt='Encerrar Expediente']"))
                )
                botao_encerrar.click()
                print("🔘 Botão 'Encerrar Expediente' clicado. Aguardando confirmação...")

                WebDriverWait(driver, 10).until(EC.alert_is_present())
                alert = driver.switch_to.alert
                print(f"🟨 Confirmação: {alert.text}")
                alert.accept()
                print("🟢 Ponto encerrado com sucesso!")
                break
            else:
                print(f"⚠️ Ainda faltam {minutos_faltando} minutos para 6 horas. Encerrando monitoramento.")
                break

    except Exception as e:
        print(f"❌ Erro durante verificação ou encerramento do ponto: {e}")
        driver.save_screenshot("erro_bater_ponto.png")
        with open("pagina_atual.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("📷 Screenshot e HTML da página salvos para análise.")

def main():
    driver = tentar_login()
    if driver:
        verificar_tempo_trabalhado(driver)
        driver.quit()
    else:
        print("❌ Não foi possível realizar login após várias tentativas.")

    print("📦 Script finalizado.")
    time.sleep(10)  # Espera 10 segundos antes de fechar o terminal

if __name__ == "__main__":
    main()
