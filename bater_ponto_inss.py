#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    UnexpectedAlertPresentException,
    TimeoutException,
    WebDriverException,
    NoSuchElementException
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


# Configurações
@dataclass
class Config:
    URL_LOGIN: str = "https://sisref.inss.gov.br/entrada.php"
    TEMPO_ESPERA_CAPTCHA: int = 6
    HORAS_TRABALHO_MINIMAS: int = 6
    MAX_TENTATIVAS_LOGIN: int = 3
    TIMEOUT_PADRAO: int = 15
    INTERVALO_VERIFICACAO: int = 5  # segundos entre verificações do relógio
    SAIR_APOS_CALCULAR_HORARIO: bool = True  # Nova opção para sair após calcular horário


# Configuração de logging
def configurar_logging():
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('ponto_inss.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )


class CredenciaisManager:
    """Gerencia credenciais de forma segura"""

    @staticmethod
    def obter_credenciais() -> Tuple[str, str]:
        """Obtém credenciais do usuário de forma segura"""
        siape = os.getenv('SIAPE_INSS', "3476995")  # Coloque seu SIAPE aqui se não usar variáveis de ambiente
        senha = os.getenv('SENHA_INSS', "gabrielg")  # Coloque sua senha aqui se não usar variáveis de ambiente

        if not siape:
            siape = input("Digite seu SIAPE: ").strip()

        if not senha:
            import getpass
            senha = getpass.getpass("Digite sua senha: ").strip()

        if not siape or not senha:
            raise ValueError("SIAPE e senha são obrigatórios")

        return siape, senha


class WebDriverManager:
    """Gerencia o WebDriver com configurações otimizadas"""

    @staticmethod
    def criar_driver() -> webdriver.Chrome:
        """Cria e configura o driver do Chrome"""
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")

        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            return driver
        except WebDriverException as e:
            logging.error(f"Erro ao criar driver: {e}")
            raise


class RelógioPontoManager:
    """Gerencia o relógio do ponto e cálculos de tempo"""

    def __init__(self):
        self.horario_entrada = None
        self.horario_saida_calculado = None

    def extrair_horario_relogio(self, texto: str) -> Optional[datetime]:
        """Extrai horário do relógio no formato HH:MM:SS"""
        try:
            # Extrai apenas a parte do horário (HH:MM:SS)
            match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', texto)
            if match:
                horas = int(match.group(1))
                minutos = int(match.group(2))
                segundos = int(match.group(3))

                # Cria um datetime com a data de hoje
                hoje = datetime.now().date()
                horario = datetime.combine(hoje, datetime.min.time().replace(
                    hour=horas, minute=minutos, second=segundos
                ))

                return horario
        except Exception as e:
            logging.error(f"Erro ao extrair horário do relógio: {e}")

        return None

    def extrair_horario_campo(self, valor: str) -> Optional[datetime]:
        """Extrai horário do campo de entrada no formato HH:MM:SS"""
        try:
            if not valor or valor.strip() == "":
                return None

            # Remove espaços e verifica se está no formato correto
            valor_limpo = valor.strip()

            # Tenta diferentes formatos
            formatos = ["%H:%M:%S", "%H:%M"]

            for formato in formatos:
                try:
                    hora_obj = datetime.strptime(valor_limpo, formato).time()
                    hoje = datetime.now().date()
                    horario = datetime.combine(hoje, hora_obj)
                    return horario
                except ValueError:
                    continue

            logging.warning(f"Formato de horário não reconhecido: {valor}")
            return None

        except Exception as e:
            logging.error(f"Erro ao extrair horário do campo: {e}")
            return None

    def calcular_horario_saida(self, horario_entrada: datetime, horas_trabalho: int = 6) -> datetime:
        """Calcula o horário de saída baseado no horário de entrada"""
        return horario_entrada + timedelta(hours=horas_trabalho)

    def definir_horario_entrada(self, horario_atual: datetime):
        """Define o horário de entrada e calcula o horário de saída"""
        if not self.horario_entrada:
            self.horario_entrada = horario_atual
            self.horario_saida_calculado = self.calcular_horario_saida(self.horario_entrada)

            logging.info(f"🕐 Horário de entrada detectado: {self.horario_entrada.strftime('%H:%M:%S')}")
            logging.info(f"🕕 Horário de saída calculado: {self.horario_saida_calculado.strftime('%H:%M:%S')}")

    def verificar_se_pode_sair(self, horario_atual: datetime) -> bool:
        """Verifica se já pode sair (completou 6 horas)"""
        if not self.horario_saida_calculado:
            return False

        return horario_atual >= self.horario_saida_calculado

    def tempo_restante(self, horario_atual: datetime) -> Optional[timedelta]:
        """Calcula o tempo restante para completar 6 horas"""
        if not self.horario_saida_calculado:
            return None

        if horario_atual >= self.horario_saida_calculado:
            return timedelta(0)

        return self.horario_saida_calculado - horario_atual

    def formatar_tempo_restante(self, tempo: timedelta) -> str:
        """Formata o tempo restante de forma legível"""
        if tempo.total_seconds() <= 0:
            return "00:00:00"

        horas = int(tempo.total_seconds() // 3600)
        minutos = int((tempo.total_seconds() % 3600) // 60)
        segundos = int(tempo.total_seconds() % 60)

        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"


class SistemaInss:
    """Classe principal para gerenciar o sistema INSS"""

    def __init__(self, config: Config):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.credenciais_manager = CredenciaisManager()
        self.relogio_manager = RelógioPontoManager()

    @contextmanager
    def gerenciar_driver(self):
        """Context manager para gerenciar o driver"""
        try:
            self.driver = WebDriverManager.criar_driver()
            yield self.driver
        finally:
            if self.driver:
                self.driver.quit()

    def realizar_login(self) -> bool:
        """Realiza login no sistema"""
        siape, senha = self.credenciais_manager.obter_credenciais()

        for tentativa in range(1, self.config.MAX_TENTATIVAS_LOGIN + 1):
            logging.info(f"Tentativa de login {tentativa}/{self.config.MAX_TENTATIVAS_LOGIN}")

            try:
                self.driver.get(self.config.URL_LOGIN)

                # Aguarda a página carregar
                WebDriverWait(self.driver, self.config.TIMEOUT_PADRAO).until(
                    EC.presence_of_element_located((By.ID, "lSiape"))
                )

                # Preenche credenciais
                campo_siape = self.driver.find_element(By.ID, "lSiape")
                campo_siape.clear()
                campo_siape.send_keys(siape)

                campo_senha = self.driver.find_element(By.ID, "lSenha")
                campo_senha.clear()
                campo_senha.send_keys(senha)

                # Aguarda CAPTCHA
                logging.info(f"⏳ Preencha o CAPTCHA manualmente em até {self.config.TEMPO_ESPERA_CAPTCHA} segundos...")
                time.sleep(self.config.TEMPO_ESPERA_CAPTCHA)

                # Clica em entrar
                botao_entrar = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[@id='btn-enviar']"))
                )
                botao_entrar.click()

                # Verifica se login foi bem-sucedido
                WebDriverWait(self.driver, 15).until(EC.url_changes(self.config.URL_LOGIN))

                logging.info("✅ Login realizado com sucesso!")
                return True

            except UnexpectedAlertPresentException:
                logging.warning("⚠️ CAPTCHA não informado ou incorreto!")
                try:
                    alert = self.driver.switch_to.alert
                    logging.info(f"Alerta: {alert.text}")
                    alert.accept()
                except Exception:
                    pass

            except TimeoutException:
                logging.error("❌ Tempo esgotado durante login")

            except Exception as e:
                logging.error(f"❌ Erro inesperado no login: {e}")
                break

        logging.error("❌ Falha no login após todas as tentativas")
        return False

    def obter_horario_ponto_entrada(self) -> Optional[datetime]:
        """Obtém o horário de entrada do ponto (quando bateu o ponto)"""
        try:
            # Procura pelo campo de entrada do ponto
            campo_entrada = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "ent"))
            )

            valor_entrada = campo_entrada.get_attribute("value")
            logging.info(f"🕐 Horário de entrada detectado no campo: {valor_entrada}")

            if valor_entrada:
                horario_entrada = self.relogio_manager.extrair_horario_campo(valor_entrada)
                if horario_entrada:
                    return horario_entrada

        except TimeoutException:
            logging.warning("Campo de entrada do ponto (id='ent') não encontrado")
        except Exception as e:
            logging.error(f"Erro ao obter horário de entrada: {e}")

        return None

    def obter_horario_relogio(self) -> Optional[datetime]:
        """Obtém o horário atual do relógio do sistema com múltiplas estratégias"""
        try:
            # Estratégia 1: Tentar o relógio principal
            try:
                elemento_relogio = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "relogio"))
                )
                texto_relogio = elemento_relogio.text
                horario = self.relogio_manager.extrair_horario_relogio(texto_relogio)
                if horario:
                    return horario
            except TimeoutException:
                pass

            # Estratégia 2: Tentar outros seletores de relógio
            seletores_relogio = [
                "#relogio",
                ".relogio",
                "*[id*='relogio']",
                "*[class*='relogio']",
                "*[id*='hora']",
                "*[class*='hora']",
                "*[id*='time']",
                "span[id*='clock']",
                "div[id*='clock']"
            ]

            for seletor in seletores_relogio:
                try:
                    elemento = self.driver.find_element(By.CSS_SELECTOR, seletor)
                    texto = elemento.text
                    if texto:
                        horario = self.relogio_manager.extrair_horario_relogio(texto)
                        if horario:
                            return horario
                except NoSuchElementException:
                    continue

            # Estratégia 3: Se não encontrar relógio, usar horário do sistema
            logging.warning("Relógio não encontrado, usando horário do sistema local")
            return datetime.now()

        except Exception as e:
            logging.error(f"Erro ao obter horário: {e}")
            return None

    def inicializar_horario_entrada(self) -> bool:
        """Inicializa o horário de entrada de forma mais robusta"""
        try:
            # Primeira tentativa: pegar do campo de entrada
            horario_entrada = self.obter_horario_ponto_entrada()

            if horario_entrada:
                self.relogio_manager.horario_entrada = horario_entrada
                self.relogio_manager.horario_saida_calculado = self.relogio_manager.calcular_horario_saida(
                    horario_entrada)

                logging.info(f"✅ Horário de entrada (do ponto): {horario_entrada.strftime('%H:%M:%S')}")
                logging.info(
                    f"🕕 Horário de saída calculado: {self.relogio_manager.horario_saida_calculado.strftime('%H:%M:%S')}")

                # NOVA FUNCIONALIDADE: Sair após calcular horário de saída
                if self.config.SAIR_APOS_CALCULAR_HORARIO:
                    logging.info("🚪 Configuração ativada: Saindo após calcular horário de saída...")
                    logging.info("✋ Programa será encerrado em 5 segundos...")
                    time.sleep(5)
                    return False  # Retorna False para encerrar o programa

                return True

            # Segunda tentativa: usar horário atual do relógio
            horario_atual = self.obter_horario_relogio()
            if horario_atual:
                self.relogio_manager.definir_horario_entrada(horario_atual)

                # NOVA FUNCIONALIDADE: Sair após calcular horário de saída
                if self.config.SAIR_APOS_CALCULAR_HORARIO:
                    logging.info("🚪 Configuração ativada: Saindo após calcular horário de saída...")
                    logging.info("✋ Programa será encerrado em 3 segundos...")
                    time.sleep(3)
                    return False  # Retorna False para encerrar o programa

                return True

            return False

        except Exception as e:
            logging.error(f"Erro ao inicializar horário de entrada: {e}")
            return False

    def encerrar_expediente(self) -> bool:
        """Encerra o expediente"""
        try:
            logging.info("\U0001F518 Tentando encerrar expediente...")

            seletores_botao = [
                "//img[@alt='Encerrar Expediente']",
                "//button[contains(text(), 'Encerrar')]",
                "//input[@value='Encerrar Expediente']",
                "//a[contains(text(), 'Encerrar')]",
                ".btn-encerrar",
                "*[alt*='Encerrar']",
                "*[title*='Encerrar']",
                "*[onclick*='encerrar']",
                "*[onclick*='Encerrar']"
            ]

            botao_encerrar = None
            for seletor in seletores_botao:
                try:
                    if seletor.startswith('//'):
                        botao_encerrar = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, seletor))
                        )
                    else:
                        botao_encerrar = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, seletor))
                        )
                    logging.info(f"✅ Botão encontrado com seletor: {seletor}")
                    break
                except TimeoutException:
                    continue

            if not botao_encerrar:
                logging.error("❌ Botão de encerrar expediente não encontrado")
                self.salvar_debug_info()
                return False

            # Clica no botão
            self.driver.execute_script("arguments[0].click();", botao_encerrar)
            logging.info("\U0001F518 Botão 'Encerrar Expediente' clicado")

            try:
                WebDriverWait(self.driver, 10).until(EC.alert_is_present())
                alert = self.driver.switch_to.alert
                logging.info(f"Confirmação: {alert.text}")
                alert.accept()
                logging.info("🟢 Expediente encerrado com sucesso!")
            except TimeoutException:
                logging.info("🟢 Expediente encerrado (sem confirmação de alerta)")

            # Aguarda campo de saída aparecer
            campo_saida = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "sai"))
            )
            valor_saida = campo_saida.get_attribute("value")
            logging.info(f"🕔 Horário de saída registrado: {valor_saida}")

            return True

        except Exception as e:
            logging.error(f"Erro ao encerrar expediente: {e}")
            self.salvar_debug_info()
            return False

    def salvar_debug_info(self):
        """Salva informações de debug"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = f"debug_screenshot_{timestamp}.png"
            html_path = f"debug_pagina_{timestamp}.html"

            self.driver.save_screenshot(screenshot_path)
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)

            logging.info(f"📷 Debug salvos: {screenshot_path}, {html_path}")
        except Exception as e:
            logging.error(f"Erro ao salvar debug: {e}")

    def monitorar_relogio(self) -> bool:
        """Monitora o relógio em tempo real e fecha o ponto automaticamente"""
        logging.info("🕐 Iniciando monitoramento do relógio...")

        # Aguarda um pouco para a página carregar completamente
        time.sleep(3)

        # Inicializa o horário de entrada de forma mais robusta
        if not self.inicializar_horario_entrada():
            logging.info("🚪 Encerrando programa conforme configuração...")
            return True  # Retorna True para indicar que foi encerrado propositalmente

        contador_verificacoes = 0
        while True:
            try:
                contador_verificacoes += 1

                # Obtém horário atual do relógio
                horario_atual = self.obter_horario_relogio()

                if not horario_atual:
                    logging.warning("⚠️ Não foi possível obter horário do relógio")
                    time.sleep(self.config.INTERVALO_VERIFICACAO)
                    continue

                # Verifica se pode sair
                if self.relogio_manager.verificar_se_pode_sair(horario_atual):
                    logging.info("🎉 Completou 6 horas de trabalho!")
                    return self.encerrar_expediente()

                # Calcula tempo restante
                tempo_restante = self.relogio_manager.tempo_restante(horario_atual)
                if tempo_restante:
                    tempo_formatado = self.relogio_manager.formatar_tempo_restante(tempo_restante)

                    # Log a cada 10 verificações para não poluir muito
                    if contador_verificacoes % 10 == 0:
                        logging.info(f"🕐 Horário atual: {horario_atual.strftime('%H:%M:%S')} | "
                                     f"Tempo restante: {tempo_formatado}")

                    # Log quando faltam poucos minutos
                    if tempo_restante.total_seconds() <= 300:  # 5 minutos
                        logging.info(f"⏰ ATENÇÃO: Faltam apenas {tempo_formatado} para completar 6 horas!")

                # Aguarda próxima verificação
                time.sleep(self.config.INTERVALO_VERIFICACAO)

            except KeyboardInterrupt:
                logging.info("🛑 Monitoramento interrompido pelo usuário")
                return False
            except Exception as e:
                logging.error(f"Erro durante monitoramento: {e}")
                time.sleep(self.config.INTERVALO_VERIFICACAO)
                continue

    def executar(self) -> bool:
        """Executa o processo completo"""
        logging.info("🚀 Iniciando sistema de ponto INSS com monitoramento inteligente...")

        try:
            with self.gerenciar_driver():
                if not self.realizar_login():
                    return False

                return self.monitorar_relogio()

        except Exception as e:
            logging.error(f"Erro geral na execução: {e}")
            return False
        finally:
            logging.info("📦 Sistema finalizado")


def main():
    """Função principal"""
    configurar_logging()

    print("=" * 60)
    print("🎯 SISTEMA INTELIGENTE DE PONTO INSS - VERSÃO MELHORADA")
    print("=" * 60)
    print("✨ Funcionalidades:")
    print("   • Captura horário exato do ponto (campo 'ent')")
    print("   • Monitora o relógio em tempo real")
    print("   • Calcula automaticamente o horário de saída")
    print("   • Fecha o ponto automaticamente às 6 horas")
    print("   • Múltiplas estratégias de detecção")
    print("   • Sistema de debug avançado")
    print("   • 🚪 NOVO: Sai automaticamente após calcular horário")
    print("=" * 60)

    try:
        config = Config()
        sistema = SistemaInss(config)

        sucesso = sistema.executar()

        if sucesso:
            logging.info("✅ Processo concluído com sucesso!")
        else:
            logging.error("❌ Processo finalizado com erros")

    except KeyboardInterrupt:
        logging.info("🛑 Programa interrompido pelo usuário")
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
    finally:
        logging.info("👋 Programa encerrado automaticamente")
        # Remove o input() para não aguardar entrada do usuário


if __name__ == "__main__":
    main()