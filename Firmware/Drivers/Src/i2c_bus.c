/*
 * i2c_bus.c — I2C1 driver (verified register-level implementation)
 * Merged from our verified polling driver into the scaffold API.
 * PB8=SCL (AF4), PB9=SDA (AF4)
 * TIMINGR from system_clock.h — correct for 40 MHz PCLK1.
 */
#include "i2c_bus.h"
#include "system_clock.h"
#include "stm32l476xx.h"

#define I2C_TIMEOUT 20000

static osbams_status_t wait_clear(volatile uint32_t *r, uint32_t f){int t=I2C_TIMEOUT;while((*r&f)&&--t);return t?OSBAMS_STATUS_OK:OSBAMS_STATUS_TIMEOUT;}
/*
 * FIX: previously checked BERR/ARLO/NACKF only AFTER the wait loop exited,
 * and the `if(!t) return TIMEOUT` branch ran BEFORE that check -- so if a
 * NACK prevented the target flag (e.g. TXIS) from ever setting, the loop
 * spun to t==0 and returned TIMEOUT without ever reaching the NACK check
 * below it. The actual cause (NACK -- e.g. wrong I2C address, device not
 * present) was silently reported as a generic timeout, which is much
 * harder to diagnose on the bench. Now checks the target flag AND every
 * error flag on every iteration, so a NACK/BERR/ARLO is reported as
 * itself the moment it appears, not only when neither it nor the target
 * flag would ever have shown up. */
static osbams_status_t wait_set(volatile uint32_t *r, uint32_t f){
    int t=I2C_TIMEOUT;
    while(t--){
        if(*r&f)return OSBAMS_STATUS_OK;
        if(I2C1->ISR&(I2C_ISR_BERR|I2C_ISR_ARLO))return OSBAMS_STATUS_BUS_ERROR;
        if(I2C1->ISR&I2C_ISR_NACKF)return OSBAMS_STATUS_NACK;
    }
    return OSBAMS_STATUS_TIMEOUT;
}
static void clear_errors(void){I2C1->ICR=I2C_ICR_BERRCF|I2C_ICR_ARLOCF|I2C_ICR_OVRCF|I2C_ICR_NACKCF|I2C_ICR_STOPCF;}

osbams_status_t I2C1_RecoverBus(void)
{
    I2C1->CR1 &= ~I2C_CR1_PE;
    for(volatile int d=0;d<1000;d++);
    GPIOB->MODER &=~(GPIO_MODER_MODE8|GPIO_MODER_MODE9);
    GPIOB->MODER |= (GPIO_MODER_MODE8_0|GPIO_MODER_MODE9_0);
    GPIOB->OTYPER|= (GPIO_OTYPER_OT8|GPIO_OTYPER_OT9);
    GPIOB->ODR   |= (1<<8)|(1<<9);
    for(int i=0;i<9;i++){
        if(GPIOB->IDR&(1<<9))break;
        GPIOB->ODR&=~(1<<8);for(volatile int d=0;d<200;d++);
        GPIOB->ODR|=(1<<8); for(volatile int d=0;d<200;d++);
    }
    GPIOB->ODR&=~(1<<9);for(volatile int d=0;d<200;d++);
    GPIOB->ODR|=(1<<9); for(volatile int d=0;d<200;d++);
    GPIOB->MODER &=~(GPIO_MODER_MODE8|GPIO_MODER_MODE9);
    GPIOB->MODER |= (GPIO_MODER_MODE8_1|GPIO_MODER_MODE9_1);
    GPIOB->AFR[1]&=~(0xFF<<0); GPIOB->AFR[1]|=(0x44<<0);
    I2C1->CR1|=I2C_CR1_PE;
    for(volatile int d=0;d<1000;d++);
    return OSBAMS_STATUS_OK;
}

void I2C1_Init(void)
{
    RCC->AHB2ENR |=RCC_AHB2ENR_GPIOBEN; RCC->APB1ENR1|=RCC_APB1ENR1_I2C1EN;
    GPIOB->MODER &=~(GPIO_MODER_MODE8|GPIO_MODER_MODE9);
    GPIOB->MODER |=(GPIO_MODER_MODE8_1|GPIO_MODER_MODE9_1);
    GPIOB->OTYPER|=(GPIO_OTYPER_OT8|GPIO_OTYPER_OT9);
    GPIOB->OSPEEDR|=(GPIO_OSPEEDR_OSPEED8|GPIO_OSPEEDR_OSPEED9);
    GPIOB->PUPDR&=~(GPIO_PUPDR_PUPD8|GPIO_PUPDR_PUPD9);
    GPIOB->AFR[1]&=~(0xFF<<0); GPIOB->AFR[1]|=(0x44<<0);
    I2C1->CR1=0;
    I2C1->TIMINGR=I2C1_TIMINGR_VALUE;  /* from system_clock.h */
    I2C1->CR1=I2C_CR1_PE|I2C_CR1_ERRIE|I2C_CR1_NACKIE;
    if(!(GPIOB->IDR&(1<<9))) I2C1_RecoverBus();
}

osbams_status_t I2C1_WriteReg(uint8_t addr, uint8_t reg, const uint8_t *data, uint8_t len)
{
    if(!data||len>7)return OSBAMS_STATUS_INVALID_ARGUMENT;
    uint8_t buf[8]; buf[0]=reg;
    for(uint8_t i=0;i<len;i++) buf[1+i]=data[i];
    osbams_status_t st=wait_clear(&I2C1->ISR,I2C_ISR_BUSY);
    if(st!=OSBAMS_STATUS_OK){I2C1_RecoverBus();return st;}
    clear_errors();
    I2C1->CR2=((addr&0xFE)<<0)|((uint32_t)(len+1)<<16)|I2C_CR2_AUTOEND|I2C_CR2_START;
    for(uint8_t i=0;i<len+1;i++){
        st=wait_set(&I2C1->ISR,I2C_ISR_TXIS);
        if(st!=OSBAMS_STATUS_OK){clear_errors();return st;}
        I2C1->TXDR=buf[i];
    }
    st=wait_set(&I2C1->ISR,I2C_ISR_STOPF);
    I2C1->ICR=I2C_ICR_STOPCF; return st;
}

osbams_status_t I2C1_ReadReg(uint8_t addr, uint8_t reg, uint8_t *data, uint8_t len)
{
    if(!data)return OSBAMS_STATUS_INVALID_ARGUMENT;
    osbams_status_t st=wait_clear(&I2C1->ISR,I2C_ISR_BUSY);
    if(st!=OSBAMS_STATUS_OK)return st;
    clear_errors();
    I2C1->CR2=((addr&0xFE)<<0)|(1UL<<16)|I2C_CR2_START;
    st=wait_set(&I2C1->ISR,I2C_ISR_TXIS);
    if(st!=OSBAMS_STATUS_OK){clear_errors();return st;}
    I2C1->TXDR=reg;
    st=wait_set(&I2C1->ISR,I2C_ISR_TC);
    if(st!=OSBAMS_STATUS_OK){clear_errors();return st;}
    I2C1->CR2=((addr&0xFE)<<0)|((uint32_t)len<<16)|I2C_CR2_RD_WRN|I2C_CR2_AUTOEND|I2C_CR2_START;
    for(uint8_t i=0;i<len;i++){
        st=wait_set(&I2C1->ISR,I2C_ISR_RXNE);
        if(st!=OSBAMS_STATUS_OK){clear_errors();return st;}
        data[i]=(uint8_t)I2C1->RXDR;
    }
    st=wait_set(&I2C1->ISR,I2C_ISR_STOPF);
    I2C1->ICR=I2C_ICR_STOPCF; return st;
}

uint8_t I2C1_Scan(uint8_t *addresses, uint8_t capacity)
{
    uint8_t found=0;
    for(uint8_t addr=0x08;addr<0x78;addr++){
        osbams_status_t st=wait_clear(&I2C1->ISR,I2C_ISR_BUSY);
        if(st!=OSBAMS_STATUS_OK) continue;
        clear_errors();
        I2C1->CR2=((uint32_t)(addr<<1)&0xFE)|(1UL<<16)|I2C_CR2_AUTOEND|I2C_CR2_START;
        for(volatile int d=0;d<5000;d++);
        if(!(I2C1->ISR&I2C_ISR_NACKF)){
            if(addresses&&found<capacity) addresses[found]=addr;
            found++;
        }
        I2C1->ICR=I2C_ICR_STOPCF|I2C_ICR_NACKCF;
    }
    return found;
}
