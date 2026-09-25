#include "tc74.h"
#include "i2c_bus.h"
#define REG_TEMP 0x00U
#define REG_CONFIG 0x01U
osbams_status_t TC74_Init(void){uint8_t c=0; osbams_status_t s=I2C1_ReadReg(TC74_I2C_ADDR,REG_CONFIG,&c,1); if(s)return s; if(c&0x80U){c&=(uint8_t)~0x80U; s=I2C1_WriteReg(TC74_I2C_ADDR,REG_CONFIG,&c,1); if(s)return s;} for(unsigned i=0;i<500U;i++){s=I2C1_ReadReg(TC74_I2C_ADDR,REG_CONFIG,&c,1); if(s)return s; if(c&0x40U)return OSBAMS_STATUS_OK;} return OSBAMS_STATUS_NOT_READY;}
osbams_status_t TC74_ReadTemperature_C10(int16_t *t){uint8_t r=0; if(!t)return OSBAMS_STATUS_INVALID_ARGUMENT; osbams_status_t s=I2C1_ReadReg(TC74_I2C_ADDR,REG_TEMP,&r,1); if(s)return s; *t=(int16_t)(int8_t)r*10; return OSBAMS_STATUS_OK;}
